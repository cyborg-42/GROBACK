"""
train_mobilenet.py
GroBack AI-IoT Smart Shelf — Banana Classifier Training Script
==============================================================
Binary classifier: Banana  |  Empty (no produce on shelf)

Dataset layout — put YOUR photos here before running:

    backend/
    └── dataset/
        ├── Banana/   ← 30-40 photos of your banana at different angles
        └── Empty/    ← 30-40 photos of the empty shelf/tray

Minimum: 30 images per folder (60 total).
More photos = better accuracy.

Run from the backend/ directory:
    python train_mobilenet.py

Output: backend/models/model.h5
"""

import os
import sys
import pathlib
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# ─── Configuration ────────────────────────────────────────────────────────────

CLASSES       = ["Banana", "Empty"]   # alphabetical so ImageDataGenerator matches
IMG_SIZE      = 128
BATCH_SIZE    = 8                     # small batch since dataset is small
EPOCHS        = 15
LEARNING_RATE = 0.0005
EARLY_STOP_PAT = 4
DATASET_DIR   = pathlib.Path("dataset")
MODEL_OUT     = pathlib.Path("models/model.h5")
MIN_IMAGES    = 30                    # minimum per class before training starts

# ─── 1. Verify dataset ────────────────────────────────────────────────────────

def verify_dataset():
    print(f"\n[STEP 1] Checking dataset at: {DATASET_DIR.resolve()}\n")
    ok = True
    for cls in CLASSES:
        cls_dir = DATASET_DIR / cls
        imgs = []
        if cls_dir.exists():
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"):
                imgs.extend(cls_dir.glob(ext))
        count = len(imgs)
        status = "OK" if count >= MIN_IMAGES else "NEED MORE PHOTOS"
        print(f"  [{status}]  {cls:10s}: {count} images  →  {cls_dir}")
        if count < MIN_IMAGES:
            ok = False

    if not ok:
        print(f"""
[ERROR] Not enough images.

  You need at least {MIN_IMAGES} photos per folder:

    backend/dataset/Banana/   ← photos of your banana
    backend/dataset/Empty/    ← photos of empty shelf

  How to add photos:
    1. Take photos with your phone camera
    2. Transfer them to the folders above (USB / WhatsApp / Google Photos)
    3. Re-run:  python train_mobilenet.py
""")
        sys.exit(1)

    print("\n  Dataset looks good — starting training!\n")


# ─── 2. Data generators ───────────────────────────────────────────────────────

def build_generators():
    """
    80/20 train/val split with aggressive augmentation on training images.
    preprocess_input scales pixels to [-1, 1] to match MobileNetV2 expectations.
    """
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        validation_split=0.2,
        rotation_range=30,
        width_shift_range=0.15,
        height_shift_range=0.15,
        zoom_range=0.20,
        horizontal_flip=True,
        brightness_range=[0.7, 1.3],  # wider range helps with shelf lighting variation
        fill_mode="nearest",
    )

    val_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,
        validation_split=0.2,
    )

    train_gen = train_datagen.flow_from_directory(
        str(DATASET_DIR),
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        seed=42,
        classes=CLASSES,
    )

    val_gen = val_datagen.flow_from_directory(
        str(DATASET_DIR),
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        seed=42,
        classes=CLASSES,
    )

    print(f"  Class map : {train_gen.class_indices}")
    print(f"  Train     : {train_gen.samples} images")
    print(f"  Validation: {val_gen.samples} images\n")
    return train_gen, val_gen


# ─── 3. Build model ───────────────────────────────────────────────────────────

def build_model():
    base = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False   # freeze — fast CPU training

    inputs = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(64, activation="relu")(x)   # smaller head for 2-class problem
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(len(CLASSES), activation="softmax")(x)

    model = models.Model(inputs, outputs, name="groback_banana_classifier")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    print(f"  Parameters: {model.count_params():,}")
    return model


# ─── 4. Train ─────────────────────────────────────────────────────────────────

def train(model, train_gen, val_gen):
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)

    cbs = [
        callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=EARLY_STOP_PAT,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ModelCheckpoint(
            filepath=str(MODEL_OUT),
            monitor="val_accuracy",
            save_best_only=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    print(f"[TRAIN] Training for up to {EPOCHS} epochs...\n")
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        callbacks=cbs,
        verbose=1,
    )
    return history


# ─── 5. Report ────────────────────────────────────────────────────────────────

def print_report(history):
    best_val  = max(history.history.get("val_accuracy", [0])) * 100
    best_train = max(history.history.get("accuracy", [0])) * 100
    n_epochs  = len(history.history.get("accuracy", []))

    print("\n" + "=" * 55)
    print("  GroBack Banana Classifier — Training Complete")
    print("=" * 55)
    print(f"  Epochs run      : {n_epochs}")
    print(f"  Best train acc  : {best_train:.1f}%")
    print(f"  Best val acc    : {best_val:.1f}%")
    print(f"  Model saved to  : {MODEL_OUT.resolve()}")
    print("=" * 55)

    if best_val < 75:
        print("\n[WARN] Accuracy below 75% — try adding more photos and re-run.")
    elif best_val < 90:
        print("\n[OK] Good accuracy. Add more varied photos to push above 90%.")
    else:
        print("\n[GREAT] Model ready for deployment!")

    print("\nNext step: python test_prediction.py <path_to_photo>\n")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  GroBack — Banana Shelf Classifier Trainer")
    print("=" * 55)

    # Create folders if they don't exist yet
    for cls in CLASSES:
        (DATASET_DIR / cls).mkdir(parents=True, exist_ok=True)

    verify_dataset()

    print("[STEP 2] Building data generators...")
    train_gen, val_gen = build_generators()

    print("[STEP 3] Building MobileNetV2 model...")
    model = build_model()

    print("[STEP 4] Training...")
    history = train(model, train_gen, val_gen)

    print_report(history)
