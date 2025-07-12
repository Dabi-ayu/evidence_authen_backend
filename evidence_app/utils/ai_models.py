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

def load_model_with_fix(model_path):
    """Robust model loading with multiple fallbacks"""
    try:
        return tf.keras.models.load_model(model_path)
    except (ValueError, TypeError) as e:
        print(f"[WARNING] Initial load failed: {str(e)}")
        print("[INFO] Attempting advanced fixes...")
        try:
            model = tf.keras.models.load_model(model_path, compile=False)
            input_shape = model.input_shape[1:]
            new_input = Input(shape=input_shape, name='fixed_input')

            x = new_input
            for layer in model.layers[1:]:
                x = layer(x)

            new_model = Model(inputs=new_input, outputs=x)
            new_model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            return new_model
        except Exception as e:
            print(f"[ERROR] Advanced fix failed: {str(e)}")
            print("[INFO] Trying last-resort weight transfer...")

            base_model = tf.keras.applications.ResNet50(
                include_top=False,
                input_shape=(224, 224, 3),
                weights=None
            )
            x = base_model.output
            x = tf.keras.layers.GlobalAveragePooling2D()(x)
            x = tf.keras.layers.Dense(1024, activation='relu')(x)
            x = tf.keras.layers.Dropout(0.5)(x)
            x = tf.keras.layers.Dense(512, activation='relu')(x)
            x = tf.keras.layers.Dropout(0.3)(x)
            output = tf.keras.layers.Dense(1, activation='sigmoid')(x)
            new_model = Model(inputs=base_model.input, outputs=output)

            new_model.load_weights(model_path)
            new_model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            return new_model

# ✅ Clear old sessions and load model
K.clear_session()
model = load_model_with_fix(MODEL_PATH)
print("[INFO] Model loaded successfully!")

def preprocess_image(img_path):
    """Preprocess image for ResNet50"""
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = img_array * 255.0
    img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
    return np.expand_dims(img_array, axis=0)

def check_tampering(image_path):
    """Run image through model and return label + confidence"""
    img_array = preprocess_image(image_path)
    prediction = model.predict(img_array, verbose=0)[0][0]
    confidence = float(prediction)
    return ('Fake', confidence) if confidence > 0.5 else ('Real', 1 - confidence)
