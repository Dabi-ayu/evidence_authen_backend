import os
import requests
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from pathlib import Path

# Define model path
MODEL_PATH = Path(__file__).resolve().parent / "vgg19.h5"

# Download the model if it doesn't exist
def download_model():
    if not MODEL_PATH.exists():
        print("Model not found. Downloading...")
        url = "https://drive.google.com/uc?export=download&id=156qm5ArGZAueKbvRj727ZOopvvOBkHI4"
        response = requests.get(url)
        response.raise_for_status()
        with open(MODEL_PATH, 'wb') as f:
            f.write(response.content)
        print("Model downloaded successfully.")

# Call download
download_model()

# Load model
model = tf.keras.models.load_model(MODEL_PATH)

def check_tampering(image_path):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    
    prediction = model.predict(img_array, verbose=0)[0][0]
    confidence = float(prediction)
    
    return ('Real', confidence) if confidence > 0.5 else ('Fake', 1 - confidence)
