import tensorflow as tf
import numpy as np
from PIL import Image
import io

def create_apple_image():
    """Create an apple-like image (red circular blob)"""
    img_height, img_width = 100, 100
    img = np.random.rand(img_height, img_width, 3) * 0.3  # Dark base

    # Create red circular blob
    center_y, center_x = np.random.randint(30, 70, 2)
    radius = np.random.randint(20, 35)

    for y in range(img_height):
        for x in range(img_width):
            dist = np.sqrt((y - center_y)**2 + (x - center_x)**2)
            if dist < radius:
                # Distinctly red color (more red, less green/yellow)
                r = min(1.0, 0.7 + np.random.rand() * 0.3)  # More red
                g = max(0.0, 0.1 + np.random.rand() * 0.2)  # Less green
                b = max(0.0, 0.05 + np.random.rand() * 0.15)  # Less blue
                img[y, x] = [r, g, b]

    return img

def create_carrot_image():
    """Create a carrot-like image (orangish, elongated/tapered)"""
    img_height, img_width = 100, 100
    img = np.random.rand(img_height, img_width, 3) * 0.3  # Dark base

    # Create carrot-like shape (triangle-ish)
    center_y, center_x = np.random.randint(40, 60), np.random.randint(30, 70)
    width_top, width_bottom = np.random.randint(8, 15), np.random.randint(20, 30)
    height = np.random.randint(30, 50)

    for y in range(img_height):
        for x in range(img_width):
            # Simple triangle shape
            dy = y - (center_y - height//2)
            dx = x - center_x

            if 0 <= dy <= height:
                width_at_y = width_top + (width_bottom - width_top) * (dy / height)
                if abs(dx) < width_at_y / 2:
                    # More distinct orange-brown color for carrot
                    r = min(1.0, 0.5 + np.random.rand() * 0.3)  # Reduced red
                    g = max(0.0, 0.2 + np.random.rand() * 0.2)  # Moderate green
                    b = max(0.0, 0.05 + np.random.rand() * 0.15)  # Low blue
                    img[y, x] = [r, g, b]

    return img

# Load the model
print("Loading model...")
model = tf.keras.models.load_model('models/model.h5')
print("Model loaded successfully!")

# Test with apple-like image
print("\nTesting apple-like image...")
img_array = create_apple_image()
img_array = tf.image.resize(img_array, (100, 100))
img_array = img_array / 255.0
img_array = np.expand_dims(img_array, axis=0)

# Get predictions
predictions = model.predict(img_array, verbose=0)[0]
class_names = ["Apple", "Banana", "Orange", "Carrot"]
result = {class_names[i]: float(predictions[i]) for i in range(len(class_names))}

print("Predictions:")
for class_name, prob in result.items():
    print(f"  {class_name}: {prob:.4f}")

pred_class = class_names[np.argmax(predictions)]
confidence = np.max(predictions) * 100
print(f"\nPrediction: {pred_class} ({confidence:.1f}%)")

# Test with carrot-like image
print("\nTesting carrot-like image...")
img_array = create_carrot_image()
img_array = tf.image.resize(img_array, (100, 100))
img_array = img_array / 255.0
img_array = np.expand_dims(img_array, axis=0)

# Get predictions
predictions = model.predict(img_array, verbose=0)[0]
result = {class_names[i]: float(predictions[i]) for i in range(len(class_names))}

print("Predictions:")
for class_name, prob in result.items():
    print(f"  {class_name}: {prob:.4f}")

pred_class = class_names[np.argmax(predictions)]
confidence = np.max(predictions) * 100
print(f"\nPrediction: {pred_class} ({confidence:.1f}%)")

# Run multiple tests
print("\nRunning multiple tests...")
correct_apples = 0
correct_carrots = 0
total_tests = 20

for i in range(total_tests):
    # Test apple
    img_array = create_apple_image()
    img_array = tf.image.resize(img_array, (100, 100))
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    predictions = model.predict(img_array, verbose=0)[0]
    pred_class = class_names[np.argmax(predictions)]
    if pred_class == "Apple":
        correct_apples += 1

    # Test carrot
    img_array = create_carrot_image()
    img_array = tf.image.resize(img_array, (100, 100))
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    predictions = model.predict(img_array, verbose=0)[0]
    pred_class = class_names[np.argmax(predictions)]
    if pred_class == "Carrot":
        correct_carrots += 1

print(f"Apple accuracy: {correct_apples}/{total_tests} ({100*correct_apples/total_tests:.1f}%)")
print(f"Carrot accuracy: {correct_carrots}/{total_tests} ({100*correct_carrots/total_tests:.1f}%)")