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

# ✅ Global model reference (pre-loaded at startup)
_model = None

def download_model_if_needed():
    """Download model from Google Drive if not found locally."""
    if not os.path.exists(MODEL_PATH):
        print("[OPTIMIZED] Downloading optimized model...")
        gdown.download(DRIVE_URL, MODEL_PATH, quiet=True)
        print("[OPTIMIZED] Download complete!")

def load_model_safely():
    """Load model once at startup with optimizations"""
    global _model
    if _model is not None:
        return _model

    download_model_if_needed()
    
    try:
        # Attempt to load as TensorFlow Lite model
        try:
            # Convert to TensorFlow Lite if not already done
            tflite_path = MODEL_PATH.replace('.h5', '.tflite')
            if not os.path.exists(tflite_path):
                print("[OPTIMIZED] Converting to TensorFlow Lite...")
                model = tf.keras.models.load_model(MODEL_PATH)
                converter = tf.lite.TFLiteConverter.from_keras_model(model)
                converter.optimizations = [tf.lite.Optimize.DEFAULT]
                tflite_model = converter.convert()
                with open(tflite_path, 'wb') as f:
                    f.write(tflite_model)
            
            # Load TFLite model
            print("[OPTIMIZED] Loading TensorFlow Lite model")
            _model = tf.lite.Interpreter(model_path=tflite_path)
            _model.allocate_tensors()
            return _model
            
        except:
            # Fallback to standard model
            print("[OPTIMIZED] Loading standard model")
            _model = tf.keras.models.load_model(MODEL_PATH)
            return _model
            
    except Exception as e:
        print(f"[CRITICAL] Model loading failed: {str(e)}")
        raise RuntimeError("Model loading failed")

# ✅ Preload model at startup
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
    """Run optimized prediction"""
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
            prediction = _model.get_tensor(output_details[0]['index'])[0][0]
        else:
            # Standard Keras prediction
            prediction = _model.predict(img_array, verbose=0)[0][0]
        
        confidence = float(prediction)
        return ('Fake', confidence) if confidence > 0.5 else ('Real', 1 - confidence)
        
    except Exception as e:
        print(f"[ERROR] Prediction failed: {str(e)}")
        return ('Error', 0.0)