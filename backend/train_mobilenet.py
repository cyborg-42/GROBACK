"""
train_mobilenet.py
GroBack AI-IoT Smart Shelf — Produce Classifier Training Script
================================================================
Trains a MobileNetV2 transfer-learning model to classify:
    Apple | Banana | Carrot | Orange

Dataset layout expected (create these folders manually and drop
your photos in — 40-60 JPG/PNG images per class is enough):

    backend/
    └── dataset/
        ├── Apple/      (e.g. apple1.jpg, apple2.jpg ...)
        ├── Banana/
        ├── Carrot/
        └── Orange/

Output:  backend/models/model.h5

Run from the backend/ directory:
    python train_mobilenet.py

Dependencies (install once):
    pip install tensorflow pillow
    pip install bing-image-downloader   # only needed for auto-download
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

CLASSES        = ["Apple", "Banana", "Carrot", "Orange"]   # must stay alphabetical for ImageDataGenerator
IMG_SIZE       = 128          # MobileNetV2 input: 128×128
BATCH_SIZE     = 16
EPOCHS         = 12
LEARNING_RATE  = 0.0005
EARLY_STOP_PAT = 3
DATASET_DIR    = pathlib.Path("dataset")
MODEL_OUT      = pathlib.Path("models/model.h5")
IMAGES_PER_CLASS = 50         # target count for auto-download

# ─── 1. Auto-download dataset (if folders are missing or empty) ────────────────

def download_dataset():
    """
    Uses bing-image-downloader to fetch ~IMAGES_PER_CLASS images per class.
    Skips any class folder that already has enough images.
    """
    try:
        from bing_image_downloader import downloader
    except ImportError:
        print("[INFO] bing-image-downloader not installed.")
        print("       Run:  pip install bing-image-downloader")
        print("       Or manually place images in dataset/<ClassName>/")
        return

    for cls in CLASSES:
        cls_dir = DATASET_DIR / cls
        existing = list(cls_dir.glob("*.[jJpP][pPnN][gG]*")) if cls_dir.exists() else []
        if len(existing) >= IMAGES_PER_CLASS:
            print(f"[SKIP] {cls}: {len(existing)} images already present.")
            continue
        needed = IMAGES_PER_CLASS - len(existing)
        print(f"[DOWNLOAD] Fetching {needed} images for '{cls}'...")
        downloader.download(
            f"{cls} fruit vegetable",
            limit=IMAGES_PER_CLASS,
            output_dir=str(DATASET_DIR),
            adult_filter_off=True,
            force_replace=False,
            timeout=60,
            verbose=False,
        )
        # bing-image-downloader saves to a subfolder named after the query;
        # rename it to the clean class name if needed.
        query_folder = DATASET_DIR / f"{cls} fruit vegetable"
        if query_folder.exists() and not cls_dir.exists():
            query_folder.rename(cls_dir)


def verify_dataset():
    """
    Checks that each class folder exists and has at least 10 images.
    Exits with a helpful message if not.
    """
    ok = True
    for cls in CLASSES:
        cls_dir = DATASET_DIR / cls
        imgs = list(cls_dir.glob("*.[jJpP][pPnN][gG]*")) if cls_dir.exists() else []
        count = len(imgs)
        status = "OK" if count >= 10 else "MISSING / TOO FEW"
        print(f"  [{status}] {cls:10s}: {count} images  ({cls_dir})")
        if count < 10:
            ok = False
    if not ok:
        print("\n[ERROR] Some classes have too few images.")
        print("  Add at least 10 JPG/PNG images per class and re-run.\n")
        sys.exit(1)


# ─── 2. Data generators with augmentation ─────────────────────────────────────

def build_generators():
    """
    Returns (train_gen, val_gen) using an 80/20 split.
    Augmentation is applied only to training images.
    Preprocessing matches MobileNetV2: pixel values scaled to [-1, 1].
    """
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,  # MobileNetV2 [-1,1] scaling
        validation_split=0.2,
        rotation_range=30,
        width_shift_range=0.15,
        height_shift_range=0.15,
        zoom_range=0.20,
        horizontal_flip=True,
        brightness_range=[0.8, 1.2],
        fill_mode="nearest",
    )

    # Validation: only preprocessing, no augmentation
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
        classes=CLASSES,   # fix the label order to match CLASSES list
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

    print(f"\n[DATA] Train samples : {train_gen.samples}")
    print(f"[DATA] Val   samples : {val_gen.samples}")
    print(f"[DATA] Class indices : {train_gen.class_indices}")
    return train_gen, val_gen


# ─── 3. Build MobileNetV2 model ───────────────────────────────────────────────

def build_model():
    """
    MobileNetV2 base (ImageNet weights, frozen) + custom classification head.
    """
    base_model = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,          # remove ImageNet softmax head
        weights="imagenet",
    )
    base_model.trainable = False    # freeze all base layers for fast CPU training

    inputs = tf.keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = base_model(inputs, training=False)  # run in inference mode even during train
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    outputs = layers.Dense(len(CLASSES), activation="softmax")(x)

    model = models.Model(inputs, outputs, name="groback_mobilenetv2")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    print("\n[MODEL] Architecture summary:")
    model.summary(line_length=80)
    return model


# ─── 4. Train ─────────────────────────────────────────────────────────────────

def train(model, train_gen, val_gen):
    """
    Trains with EarlyStopping and saves the best checkpoint.
    """
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

    print(f"\n[TRAIN] Starting training for up to {EPOCHS} epochs...")
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        callbacks=cbs,
        verbose=1,
    )
    return history


# ─── 5. Post-training report ──────────────────────────────────────────────────

def print_report(history):
    best_val_acc = max(history.history.get("val_accuracy", [0])) * 100
    best_train_acc = max(history.history.get("accuracy", [0])) * 100
    epochs_run = len(history.history.get("accuracy", []))

    print("\n" + "=" * 60)
    print("  GroBack MobileNetV2 Training Complete")
    print("=" * 60)
    print(f"  Epochs run        : {epochs_run}")
    print(f"  Best train acc    : {best_train_acc:.1f}%")
    print(f"  Best val   acc    : {best_val_acc:.1f}%")
    print(f"  Model saved to    : {MODEL_OUT.resolve()}")
    print("=" * 60)

    if best_val_acc < 70:
        print("\n[WARN] Validation accuracy is below 70%.")
        print("       Try adding more images (aim for 60+ per class) and re-run.")
    else:
        print("\n[OK] Model is ready. Run test_prediction.py to verify.")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  GroBack — MobileNetV2 Produce Classifier Trainer")
    print("=" * 60)

    # Step 1: ensure dataset exists
    print(f"\n[STEP 1] Checking dataset at: {DATASET_DIR.resolve()}")
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    for cls in CLASSES:
        (DATASET_DIR / cls).mkdir(exist_ok=True)

    download_dataset()
    verify_dataset()

    # Step 2: build data pipelines
    print("\n[STEP 2] Building data generators...")
    train_gen, val_gen = build_generators()

    # Step 3: build model
    print("\n[STEP 3] Building MobileNetV2 model...")
    model = build_model()

    # Step 4: train
    print("\n[STEP 4] Training...")
    history = train(model, train_gen, val_gen)

    # Step 5: report
    print_report(history)
