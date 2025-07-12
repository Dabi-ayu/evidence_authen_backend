import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os
from tensorflow.keras import backend as K
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'deepfake_detection_resnet50.h5')

def load_model_with_fix(model_path):
    """Robust model loading with multiple fallbacks"""
    try:
        # Try standard loading
        return tf.keras.models.load_model(model_path)
    except (ValueError, TypeError) as e:
        print(f"Initial load failed: {str(e)}")
        print("Attempting advanced fixes...")
        
        try:
            # 1. Load without compilation
            model = tf.keras.models.load_model(model_path, compile=False)
            
            # 2. Rebuild model with new input layer
            input_shape = model.input_shape[1:]  # Get (224, 224, 3)
            new_input = Input(shape=input_shape, name='fixed_input')
            
            # 3. Reconnect all layers
            x = new_input
            for layer in model.layers[1:]:  # Skip original input layer
                x = layer(x)
            
            # 4. Create new model
            new_model = Model(inputs=new_input, outputs=x)
            
            # 5. Recompile with original parameters
            new_model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            return new_model
        except Exception as e:
            print(f"Advanced fix failed: {str(e)}")
            print("Trying last-resort weight transfer...")
            
            # 6. Create model architecture from scratch
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
            
            # 7. Load weights only
            new_model.load_weights(model_path)
            new_model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy']
            )
            return new_model

# Clear previous sessions
K.clear_session()

# Load model
model = load_model_with_fix(MODEL_PATH)
print("Model loaded successfully!")

def preprocess_image(img_path):
    """Preprocess image matching training pipeline"""
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    
    # Apply ResNet50-specific preprocessing
    img_array = img_array * 255.0  # Scale to 0-255
    img_array = tf.keras.applications.resnet50.preprocess_input(img_array)
    
    return np.expand_dims(img_array, axis=0)

def check_tampering(image_path):
    """Check if image is real or fake"""
    img_array = preprocess_image(image_path)
    prediction = model.predict(img_array, verbose=0)[0][0]
    confidence = float(prediction)
    
    # Return results (confidence > 0.5 = Fake)
    if confidence > 0.5:
        return 'Fake', confidence
    else:
        return 'Real', 1 - confidence