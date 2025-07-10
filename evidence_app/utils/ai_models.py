import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os
import requests
from pathlib import Path

# Define where to store/load the model
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / 'vgg19.h5'

# ✅ Download model if not present
def download_model():
    if not MODEL_PATH.exists():
        print("Downloading VGG19 model...")
        url = "https://drive.google.com/file/d/1cX2AQ67R_hCKXxb2tcVhQUjUUdkpkeeS/view/vgg19.h5"  # 🔁 Replace with a real download URL
        response = requests.get(url)
        response.raise_for_status()
        with open(MODEL_PATH, 'wb') as f:
            f.write(response.content)
        print("Model download complete.")

download_model()

# ✅ Load model
model = tf.keras.models.load_model(MODEL_PATH)

# ✅ Function to check tampering
def check_tampering(image_path):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    
    prediction = model.predict(img_array, verbose=0)[0][0]
    confidence = float(prediction)
    
    return ('Real', confidence) if confidence > 0.5 else ('Fake', 1 - confidence)
