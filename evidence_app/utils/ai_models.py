import os
import numpy as np
import tensorflow as tf
import gdown
from PIL import Image
from io import BytesIO

# ✅ Model file setup
MODEL_FILE_NAME = 'deepfake_detection_resnet50.h5'
MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_FILE_NAME)
DRIVE_FILE_ID = '1MaD9ZpejHMoULsSlD8ipMRTDkk8QAeyt'
DRIVE_URL = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'

# ✅ Global model reference
_model = None

def download_model_if_needed():
    if not os.path.exists(MODEL_PATH):
        print("[INFO] Downloading model...")
        gdown.download(DRIVE_URL, MODEL_PATH, quiet=True)
        print("[INFO] Download complete!")

def build_model_from_scratch():
    """Build model architecture manually to avoid loading issues"""
    print("[FALLBACK] Building model from scratch...")
    input_tensor = tf.keras.layers.Input(shape=(224, 224, 3))
    base_model = tf.keras.applications.ResNet50(
        include_top=False,
        input_tensor=input_tensor,
        weights=None
    )
    x = base_model.output
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(1024, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.5)(x)
    x = tf.keras.layers.Dense(512, activation='relu')(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    output = tf.keras.layers.Dense(1, activation='sigmoid')(x)
    
    model = tf.keras.models.Model(inputs=input_tensor, outputs=output)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

def load_model_safely():
    """Robust model loader with enhanced error handling"""
    global _model
    if _model is not None:
        return _model

    download_model_if_needed()
    
    try:
        # First try standard load with workaround
        try:
            print("[TRY] Loading with compile=False")
            _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
            print("[SUCCESS] Model loaded with compile=False")
        except (TypeError, ValueError) as e:
            if 'batch_shape' in str(e):
                print("[FALLBACK] Handling batch_shape error")
                # Build architecture then load weights
                _model = build_model_from_scratch()
                _model.load_weights(MODEL_PATH)
                print("[SUCCESS] Weights loaded on custom architecture")
            else:
                raise
                
        # Now try converting to TensorFlow Lite
        try:
            tflite_path = MODEL_PATH.replace('.h5', '.tflite')
            if not os.path.exists(tflite_path):
                print("[OPTIMIZE] Converting to TensorFlow Lite")
                converter = tf.lite.TFLiteConverter.from_keras_model(_model)
                converter.optimizations = [tf.lite.Optimize.DEFAULT]
                tflite_model = converter.convert()
                with open(tflite_path, 'wb') as f:
                    f.write(tflite_model)
                    
                print("[OPTIMIZE] Loading TensorFlow Lite model")
                _model = tf.lite.Interpreter(model_path=tflite_path)
                _model.allocate_tensors()
            else:
                print("[OPTIMIZE] Using existing TensorFlow Lite model")
                _model = tf.lite.Interpreter(model_path=tflite_path)
                _model.allocate_tensors()
                
        except Exception as e:
            print(f"[WARNING] TFLite conversion failed, using original: {str(e)}")
            # Keep the original model if conversion fails
            
        return _model
        
    except Exception as e:
        print(f"[CRITICAL] Final model loading failed: {str(e)}")
        raise RuntimeError("All model loading attempts failed")

# Preload model at startup
print("[INIT] Preloading model...")
load_model_safely()
print("[INIT] Model preloaded successfully")

def preprocess_image(image_data):
    """Optimized in-memory image processing"""
    try:
        # Process without disk I/O
        img = Image.open(BytesIO(image_data)).convert('RGB')
        
        # Resize to model input size
        img = img.resize((224, 224))
        
        # Convert to array and normalize
        img_array = np.array(img) / 255.0
        
        # Expand dimensions for batch
        return np.expand_dims(img_array, axis=0)
    except Exception as e:
        print(f"[ERROR] Image processing failed: {str(e)}")
        return None

def check_tampering(image_data):
    """Run prediction and return label with confidence"""
    try:
        # 1. Preprocess image in memory
        img_array = preprocess_image(image_data)
        if img_array is None:
            return ('Error', 0.0)

        # 2. Run prediction based on model type
        if isinstance(_model, tf.lite.Interpreter):
            # TensorFlow Lite prediction
            input_details = _model.get_input_details()
            output_details = _model.get_output_details()
            
            _model.set_tensor(input_details[0]['index'], img_array.astype(np.float32))
            _model.invoke()
            prediction = _model.get_tensor(output_details[0]['index'])
            confidence = float(prediction[0][0])  # Extract single value
        else:
            # Standard Keras prediction
            prediction = _model.predict(img_array, verbose=0)
            confidence = float(prediction[0][0])  # For sigmoid output
        
        # 3. Interpret results with confidence
        if confidence > 0.5:
            return ('Fake', confidence)
        else:
            return ('Real', 1 - confidence)
        
    except Exception as e:
        print(f"[ERROR] Prediction failed: {str(e)}")
        return ('Error', 0.0)