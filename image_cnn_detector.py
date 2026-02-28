import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os

class ImageCNNDetector:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        print("🔄 Loading CNN model...")
        self.model = tf.keras.models.load_model(model_path)
        print("✅ Model loaded successfully")

    def predict(self, image_path):
        try:
            img = image.load_img(image_path, target_size=(224, 224))
            img_array = image.img_to_array(img)

            img_array = img_array / 255.0
            img_array = np.expand_dims(img_array, axis=0)

            prediction = self.model.predict(img_array)[0][0]

            # fake = 0, real = 1
            is_ai = prediction < 0.5
            confidence = float((1 - prediction) * 100 if is_ai else prediction * 100)

            print("Raw prediction:", prediction)

            return {
                "isAI": bool(is_ai),
                "confidence": round(confidence, 2),
                "verdict": "AI Generated" if is_ai else "Real/Human Created",
                "details": "CNN-based image classification result",
                "indicators": []
            }

        except Exception as e:
            return {"error": str(e)}
