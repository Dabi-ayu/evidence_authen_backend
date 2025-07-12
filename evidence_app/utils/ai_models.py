import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os

# Use raw string for Windows paths and make it relative
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'vgg19.h5')
model = tf.keras.models.load_model(MODEL_PATH)

def check_tampering(image_path):
    img = image.load_img(image_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    
    prediction = model.predict(img_array, verbose=0)[0][0]
    confidence = float(prediction)
    
    return ('Real', confidence) if confidence > 0.5 else ('Fake', 1 - confidence)