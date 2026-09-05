"""
Create a simple CNN model for apple detection
This generates synthetic training data and trains a model to recognize apples
vs other fruits (banana, orange, carrot) based on color and shape features.
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os

def generate_synthetic_data(num_samples=1000):
    """Generate synthetic apple and non-apple images"""
    print(f"Generating {num_samples} synthetic training samples...")

    # Image dimensions expected by the model
    img_height, img_width = 100, 100

    # Arrays to hold data
    images = []
    labels = []

    # Class names: 0=Apple, 1=Banana, 2=Orange, 3=Carrot
    class_names = ["Apple", "Banana", "Orange", "Carrot"]

    for i in range(num_samples):
        # Create base image
        img = np.random.rand(img_height, img_width, 3) * 0.3  # Dark base

        # Randomly select class
        class_idx = np.random.randint(0, 4)

        if class_idx == 0:  # Apple - distinctly red, round-ish
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

        elif class_idx == 1:  # Banana - yellowish, elongated
            # Create yellow elliptical blob
            center_y, center_x = np.random.randint(30, 70, 2)
            radius_y, radius_x = np.random.randint(15, 25), np.random.randint(25, 40)
            angle = np.random.rand() * np.pi  # Random rotation

            for y in range(img_height):
                for x in range(img_width):
                    # Rotated ellipse
                    dx = x - center_x
                    dy = y - center_y
                    cos_a, sin_a = np.cos(angle), np.sin(angle)
                    xr = dx * cos_a + dy * sin_a
                    yr = -dx * sin_a + dy * cos_a

                    if (xr/radius_x)**2 + (yr/radius_y)**2 < 1:
                        # Yellowish color
                        r = min(1.0, 0.8 + np.random.rand() * 0.2)
                        g = min(1.0, 0.8 + np.random.rand() * 0.2)
                        b = max(0.0, 0.2 + np.random.rand() * 0.3)
                        img[y, x] = [r, g, b]

        elif class_idx == 2:  # Orange - orange-ish, round
            # Create orange circular blob
            center_y, center_x = np.random.randint(30, 70, 2)
            radius = np.random.randint(20, 35)

            for y in range(img_height):
                for x in range(img_width):
                    dist = np.sqrt((y - center_y)**2 + (x - center_x)**2)
                    if dist < radius:
                        # Orange-ish color
                        r = min(1.0, 0.7 + np.random.rand() * 0.3)
                        g = max(0.0, 0.4 + np.random.rand() * 0.4)
                        b = max(0.0, 0.1 + np.random.rand() * 0.3)
                        img[y, x] = [r, g, b]

        else:  # Carrot - orange-brown, tapered
            # Create carrot-like shape (more distinct triangle)
            center_y, center_x = np.random.randint(40, 60), np.random.randint(30, 70)
            width_top, width_bottom = np.random.randint(6, 12), np.random.randint(15, 25)
            height = np.random.randint(35, 55)

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

        images.append(img)
        labels.append(class_idx)

        if (i + 1) % 200 == 0:
            print(f"  Generated {i + 1}/{num_samples} samples")

    # Convert to numpy arrays
    images = np.array(images, dtype=np.float32)
    labels = np.array(labels, dtype=np.int32)

    # Convert labels to categorical
    labels_categorical = keras.utils.to_categorical(labels, num_classes=4)

    print(f"Generated {len(images)} images with shape {images.shape}")
    print(f"Labels distribution: {np.bincount(labels)}")

    return images, labels_categorical

def create_model():
    """Create a simple CNN model for fruit classification"""
    model = keras.Sequential([
        # Input layer
        layers.Input(shape=(100, 100, 3)),

        # First convolutional block
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),

        # Second convolutional block
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),

        # Third convolutional block
        layers.Conv2D(64, (3, 3), activation='relu'),

        # Flatten and dense layers
        layers.Flatten(),
        layers.Dense(64, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(4, activation='softmax')  # 4 classes: Apple, Banana, Orange, Carrot
    ])

    return model

def main():
    # Set random seeds for reproducibility
    np.random.seed(42)
    tf.random.set_seed(42)

    # Generate synthetic training data
    print("Creating synthetic training data for apple detection...")
    X_train, y_train = generate_synthetic_data(num_samples=1200)

    # Generate validation data
    print("Creating validation data...")
    X_val, y_val = generate_synthetic_data(num_samples=300)

    # Create model
    print("Creating CNN model...")
    model = create_model()

    # Compile model
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # Print model summary
    print("\nModel Architecture:")
    model.summary()

    # Train model
    print("\nTraining model...")
    history = model.fit(
        X_train, y_train,
        batch_size=32,
        epochs=15,
        validation_data=(X_val, y_val),
        verbose=1
    )

    # Evaluate model
    print("\nEvaluating model...")
    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
    print(f"Validation Accuracy: {val_acc:.4f}")
    print(f"Validation Loss: {val_loss:.4f}")

    # Save model
    model_path = "models/model.h5"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    print(f"\nModel saved to: {model_path}")

    # Test with a few samples
    print("\nTesting model predictions...")
    test_pred = model.predict(X_val[:5])
    class_names = ["Apple", "Banana", "Orange", "Carrot"]

    for i in range(5):
        pred_class = np.argmax(test_pred[i])
        confidence = test_pred[i][pred_class] * 100
        true_class = np.argmax(y_val[i])
        print(f"Sample {i+1}: Predicted={class_names[pred_class]} ({confidence:.1f}%), "
              f"Actual={class_names[true_class]}")

if __name__ == "__main__":
    main()