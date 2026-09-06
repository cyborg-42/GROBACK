"""
test_prediction.py
GroBack AI-IoT Smart Shelf — Model Verification Script
=======================================================
Loads backend/models/model.h5 and runs inference on a real image.
Preprocessing is identical to train_mobilenet.py and main.py.

Usage (run from backend/ directory):
    python test_prediction.py <path_to_image>

Examples:
    python test_prediction.py banana1.jpg
    python test_prediction.py C:/Users/You/Pictures/shelf_empty.jpg

If no image path is given, two synthetic colour patches are tested
(yellow for Banana, grey for Empty) as a basic sanity check.
"""

import sys
import pathlib
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# ─── Constants — must match train_mobilenet.py exactly ───────────────────────
CLASSES    = ["Banana", "Empty"]
MODEL_PATH = pathlib.Path("models/model.h5")

# ─── Load model ───────────────────────────────────────────────────────────────

def load_model():
    if not MODEL_PATH.exists():
        print(f"\n[ERROR] Model not found at {MODEL_PATH.resolve()}")
        print("  Run train_mobilenet.py first, then come back here.\n")
        sys.exit(1)

    print(f"\n[OK] Loading model from {MODEL_PATH.resolve()} ...")
    model = tf.keras.models.load_model(str(MODEL_PATH))

    # Read actual input size from the model — works for both 100x100 and 128x128
    size = model.input_shape[1]
    n_classes = model.output_shape[-1]
    print(f"[OK] Input shape : {model.input_shape}")
    print(f"[OK] Classes     : {n_classes} ({', '.join(CLASSES[:n_classes])})")

    if n_classes != len(CLASSES):
        print(f"[WARN] Model has {n_classes} outputs but CLASSES has {len(CLASSES)}. "
              f"Using first {n_classes} class names.")

    return model, size, n_classes

# ─── Preprocessing ────────────────────────────────────────────────────────────

def preprocess_image(image_path: str, size: int) -> np.ndarray:
    """
    Resize to size×size, convert to RGB, apply MobileNetV2 preprocess_input
    (scales pixels to [-1, 1]). Returns array of shape (1, size, size, 3).
    """
    img = Image.open(image_path).convert("RGB").resize((size, size))
    arr = np.array(img, dtype=np.float32)
    arr = preprocess_input(arr)
    return np.expand_dims(arr, axis=0)

# ─── Predict ──────────────────────────────────────────────────────────────────

def predict(model, image_path: str, size: int, n_classes: int):
    class_names = CLASSES[:n_classes]

    print(f"\n[IMAGE] {image_path}")
    arr   = preprocess_image(image_path, size)
    preds = model.predict(arr, verbose=0)[0]

    print("\n  Confidence scores:")
    print("  " + "─" * 36)
    for cls, prob in sorted(zip(class_names, preds), key=lambda x: -x[1]):
        bar = "█" * int(prob * 30)
        print(f"  {cls:<10} {prob * 100:6.2f}%  {bar}")
    print("  " + "─" * 36)

    top_cls  = class_names[int(np.argmax(preds))]
    top_conf = float(np.max(preds)) * 100

    if top_cls == "Banana":
        emoji = "🍌"
    else:
        emoji = "📭"

    print(f"\n  {emoji}  Prediction : {top_cls}  ({top_conf:.1f}% confidence)")

    if top_conf < 60:
        print("  ⚠️  Low confidence — add more training photos and retrain.")

    return top_cls, top_conf

# ─── Synthetic sanity check ───────────────────────────────────────────────────

def sanity_check(model, size: int, n_classes: int):
    """
    Runs two synthetic patches through the model when no image is supplied.
    Not a substitute for real image testing — just confirms the model runs.
    """
    class_names = CLASSES[:n_classes]

    print("\n[INFO] No image supplied — running synthetic sanity check.")
    print("       Pass a real photo path for a meaningful result.\n")

    patches = {
        "Yellow patch (should → Banana)": [220, 200,  50],
        "Grey   patch (should → Empty) ": [180, 180, 180],
    }

    print("  " + "─" * 50)
    for label, rgb in patches.items():
        patch = np.full((size, size, 3), rgb, dtype=np.float32)
        patch = preprocess_input(patch)
        arr   = np.expand_dims(patch, axis=0)
        preds = model.predict(arr, verbose=0)[0]
        top   = class_names[int(np.argmax(preds))]
        conf  = float(np.max(preds)) * 100
        all_scores = "  |  ".join(
            f"{c}: {p*100:.1f}%" for c, p in zip(class_names, preds)
        )
        print(f"  {label}")
        print(f"    → {top} ({conf:.1f}%)   [{all_scores}]")
    print("  " + "─" * 50)
    print("\n[INFO] Sanity check complete.\n")

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model, size, n_classes = load_model()

    if len(sys.argv) < 2:
        sanity_check(model, size, n_classes)
    else:
        path = sys.argv[1]
        if not pathlib.Path(path).exists():
            print(f"\n[ERROR] File not found: {path}")
            sys.exit(1)
        predict(model, path, size, n_classes)
