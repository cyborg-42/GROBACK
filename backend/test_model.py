import tensorflow as tf
import numpy as np
from PIL import Image
import io

# Load the model
print("Loading model...")
model = tf.keras.models.load_model('models/model.h5')
print("Model loaded successfully!")

# Test with a simple red image (should predict apple)
print("\nCreating test image (red - should predict apple)...")
img_array = np.zeros((100, 100, 3), dtype=np.uint8)
img_array[:, :] = [200, 50, 50]  # Reddish color

img = Image.fromarray(img_array)
img_array = np.array(img)
img_array = tf.image.resize(img_array, (100, 100))
img_array = img_array / 255.0
img_array = np.expand_dims(img_array, axis=0)

# Get predictions
predictions = model.predict(img_array, verbose=0)[0]
class_names = ["Apple", "Banana", "Orange", "Carrot"]
result = {class_names[i]: float(predictions[i]) for i in range(len(class_names))}

print("\nPredictions:")
for class_name, prob in result.items():
    print(f"  {class_name}: {prob:.4f}")

pred_class = class_names[np.argmax(predictions)]
confidence = np.max(predictions) * 100
print(f"\nPrediction: {pred_class} ({confidence:.1f}%)")

# Test with orange image (should predict carrot or orange)
print("\nCreating test image (orange - should predict carrot or orange)...")
img_array = np.zeros((100, 100, 3), dtype=np.uint8)
img_array[:, :] = [200, 100, 50]  # Orangish color

img = Image.fromarray(img_array)
img_array = np.array(img)
img_array = tf.image.resize(img_array, (100, 100))
img_array = img_array / 255.0
img_array = np.expand_dims(img_array, axis=0)

# Get predictions
predictions = model.predict(img_array, verbose=0)[0]
result = {class_names[i]: float(predictions[i]) for i in range(len(class_names))}

print("\nPredictions:")
for class_name, prob in result.items():
    print(f"  {class_name}: {prob:.4f}")

pred_class = class_names[np.argmax(predictions)]
confidence = np.max(predictions) * 100
print(f"\nPrediction: {pred_class} ({confidence:.1f}%)")