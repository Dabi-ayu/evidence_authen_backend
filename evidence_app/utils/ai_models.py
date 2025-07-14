import os
import numpy as np
import tensorflow as tf
import gdown
from tensorflow.keras.preprocessing import image
from tensorflow.keras import backend as K
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input
from PIL import Image
import gc

# ✅ Model file setup
MODEL_FILE_NAME = 'deepfake_detection_resnet50.h5'
MODEL_PATH = os.path.join(os.path.dirname(__file__), MODEL_FILE_NAME)
DRIVE_FILE_ID = '1MaD9ZpejHMoULsSlD8ipMRTDkk8QAeyt'
DRIVE_URL = f'https://drive.google.com/uc?id={DRIVE_FILE_ID}'

# ✅ Global model reference (lazy-loaded)
_model = None

def download_model_if_needed():
    """Download model from Google Drive if not found locally."""
    if not os.path.exists(MODEL_PATH):
        print("[INFO] Model not found locally. Downloading from Google Drive...")
        gdown.download(DRIVE_URL, MODEL_PATH, quiet=False)
        print("[INFO] Download complete!")

def load_model_safely():
    """Load model safely with fallback strategy."""
    global _model

    if _model is not None:
        return _model  # Already loaded

    # Step 1: Download if missing
    download_model_if_needed()

    # Step 2: Clear old Keras sessions
    K.clear_session()

    try:
        # Try standard full model load
        _model = tf.keras.models.load_model(MODEL_PATH)
        print("[INFO] Model loaded successfully (full model).")
    except (ValueError, TypeError, OSError) as e:
        print(f"[WARNING] Full model load failed: {str(e)}")
        print("[INFO] Attempting to load model weights only...")
        try:
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

            _model = Model(inputs=input_tensor, outputs=output)
            _model.load_weights(MODEL_PATH)
            _model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            print("[INFO] Model weights loaded successfully!")
        except Exception as ex:
            print(f"[CRITICAL] Weight loading failed: {str(ex)}")
            _model = None
            raise RuntimeError("Unable to load model or weights.")

    return _model

def resize_image_for_memory(img_path):
    """Resize image to a smaller size before processing to reduce memory usage."""
    try:
        with Image.open(img_path) as img:
            img = img.convert('RGB')  # Ensure 3 channels
            img = img.resize((600, 600))  # Resize to smaller size (adjust if needed)
            img.save(img_path)
        print("[INFO] Image resized to reduce memory usage.")
    except Exception as e:
        print(f"[WARNING] Failed to resize image: {str(e)}")

def preprocess_image(img_path):
    """Preprocess image for ResNet50."""
    model = load_model_safely()
    if model is None:
        raise RuntimeError("Model not loaded - cannot preprocess image.")

    # Resize image to reduce memory pressure
    resize_image_for_memory(img_path)

    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
    return np.expand_dims(img_array, axis=0)

def check_tampering(image_path):
    """Run image through model and return label + confidence."""
    try:
        model = load_model_safely()
        if model is None:
            return ('Error', 0.0)

        img_array = preprocess_image(image_path)
        prediction = model.predict(img_array, verbose=0)[0][0]
        confidence = float(prediction)

        # Clear TensorFlow session and collect garbage to free memory
        K.clear_session()
        gc.collect()

        return ('Fake', confidence) if confidence > 0.5 else ('Real', 1 - confidence)
    except Exception as e:
        print(f"[ERROR] Prediction failed: {str(e)}")
        return ('Error', 0.0)
