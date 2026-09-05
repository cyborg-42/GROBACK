"""
test_prediction.py
GroBack AI-IoT Smart Shelf — Standalone Model Verification Script
=================================================================
Loads backend/models/model.h5 and runs inference on a real image file.
Preprocessing is identical to train_mobilenet.py and main.py.

Usage (from backend/ directory):
    python test_prediction.py <path_to_image>

Examples:
    python test_prediction.py test_apple.jpg
    python test_prediction.py C:/Users/You/Pictures/orange.jpg

If no image path is given, a synthetic test image is used for each class
to sanity-check that the model loads and outputs valid probabilities.
"""

import sys
import pathlib
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# ─── Constants — must match train_mobilenet.py exactly ───────────────────────
CLASSES   = ["Apple", "Banana", "Carrot", "Orange"]
IMG_SIZE  = 128
MODEL_PATH = pathlib.Path("models/model.h5")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_model():
    if not MODEL_PATH.exists():
        print(f"[ERROR] Model not found at {MODEL_PATH.resolve()}")
        print("        Run train_mobilenet.py first.")
        sys.exit(1)
    print(f"[OK] Loading model from {MODEL_PATH.resolve()} ...")
    model = tf.keras.models.load_model(str(MODEL_PATH))
    print(f"[OK] Model loaded. Input shape: {model.input_shape}")
    return model


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load an image file and apply the exact same preprocessing used during
    training: resize to 128×128, convert to RGB, apply MobileNetV2
    preprocess_input (scales pixels to [-1, 1]).

    Returns a float32 array of shape (1, 128, 128, 3).
    """
    img = Image.open(image_path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    arr = np.array(img, dtype=np.float32)           # shape: (128, 128, 3)
    arr = preprocess_input(arr)                      # scale to [-1, 1]
    return np.expand_dims(arr, axis=0)               # shape: (1, 128, 128, 3)


def predict(model, image_path: str):
    print(f"\n[IMAGE] {image_path}")
    img_array = preprocess_image(image_path)
    preds = model.predict(img_array, verbose=0)[0]   # shape: (4,)

    print("\n  Confidence scores:")
    print("  " + "─" * 32)
    for cls, prob in sorted(zip(CLASSES, preds), key=lambda x: -x[1]):
        bar = "█" * int(prob * 30)
        print(f"  {cls:<10} {prob * 100:6.2f}%  {bar}")
    print("  " + "─" * 32)

    top_idx = int(np.argmax(preds))
    top_cls = CLASSES[top_idx]
    top_conf = preds[top_idx] * 100
    print(f"\n  ✅ Prediction : {top_cls}  ({top_conf:.1f}% confidence)")

    if top_conf < 60:
        print("  ⚠️  Low confidence — consider adding more training images.")
    return top_cls, top_conf


def run_synthetic_sanity_check(model):
    """
    When no image path is supplied, run 4 synthetic colour patches
    (one per class colour) through the model and print results.
    Not expected to be accurate — just verifies the model runs without error.
    """
    print("\n[INFO] No image supplied — running synthetic sanity check.")
    print("       (Results on solid-colour patches are not meaningful.)\n")

    synthetic = {
        "Apple  (red patch)" : [200,  50,  50],
        "Banana (yellow)    ": [220, 200,  50],
        "Carrot (orange)    ": [220, 130,  40],
        "Orange (orange)    ": [240, 130,  30],
    }

    for label, rgb in synthetic.items():
        patch = np.full((IMG_SIZE, IMG_SIZE, 3), rgb, dtype=np.float32)
        patch = preprocess_input(patch)
        arr   = np.expand_dims(patch, axis=0)
        preds = model.predict(arr, verbose=0)[0]
        top   = CLASSES[int(np.argmax(preds))]
        conf  = float(np.max(preds)) * 100
        print(f"  {label}  →  {top} ({conf:.1f}%)")

    print("\n[INFO] Sanity check done. Pass a real image path for a proper test.")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = load_model()

    if len(sys.argv) < 2:
        run_synthetic_sanity_check(model)
    else:
        image_path = sys.argv[1]
        if not pathlib.Path(image_path).exists():
            print(f"[ERROR] File not found: {image_path}")
            sys.exit(1)
        predict(model, image_path)
