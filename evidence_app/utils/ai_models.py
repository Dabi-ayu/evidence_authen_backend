import os
import numpy as np
import tensorflow as tf
import gdown
from tensorflow.keras.preprocessing import image
from tensorflow.keras import backend as K
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input

# ✅ Google Drive Setup
MODEL_FILE_NAME = 'deepfake_detection_resnet50.h5'
MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_FILE_NAME)

# ✅ Google Drive file ID
DRIVE_FILE_ID = '1MaD9ZpejHMoULsSlD8ipMRTDkk8QAeyt'
DRIVE_URL = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'

# ✅ Download model if not found locally
if not os.path.exists(MODEL_PATH):
    print("[INFO] Model not found locally. Downloading from Google Drive...")
    gdown.download(DRIVE_URL, MODEL_PATH, quiet=False)
    print("[INFO] Download complete!")

def load_model_safely(model_path):
    """Robust model loading with multiple fallbacks"""
    try:
        # Try standard loading first
        return tf.keras.models.load_model(model_path)
    except (ValueError, TypeError, OSError) as e:
        print(f"[WARNING] Initial load failed: {str(e)}")
    
    try:
        print("[INFO] Attempting to load model weights only...")
        # Build model architecture
        input_tensor = Input(shape=(224, 224, 3), name='input')
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
        model = Model(inputs=input_tensor, outputs=output)
        
        # Load weights only
        model.load_weights(model_path)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        return model
    except Exception as e:
        print(f"[ERROR] Weight loading failed: {str(e)}")
        raise RuntimeError("Unable to load model weights. Please check model compatibility.")

# ✅ Clear old sessions and load model
K.clear_session()
try:
    model = load_model_safely(MODEL_PATH)
    print("[INFO] Model loaded successfully!")
except Exception as e:
    print(f"[CRITICAL] Model loading failed: {str(e)}")
    model = None

def preprocess_image(img_path):
    """Preprocess image for ResNet50"""
    if model is None:
        raise RuntimeError("Model not loaded - cannot process image")
        
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
    return np.expand_dims(img_array, axis=0)

def check_tampering(image_path):
    """Run image through model and return label + confidence"""
    if model is None:
        return ('Error', 0.0)
    
    try:
        img_array = preprocess_image(image_path)
        prediction = model.predict(img_array, verbose=0)[0][0]
        confidence = float(prediction)
        return ('Fake', confidence) if confidence > 0.5 else ('Real', 1 - confidence)
    except Exception as e:
        print(f"[ERROR] Prediction failed: {str(e)}")
        return ('Error', 0.0)