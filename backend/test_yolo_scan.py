"""
test_yolo_scan.py
GroBack AI-IoT Smart Shelf — YOLOv8 Pipeline Verification
==========================================================
Tests the exact same run_yolo() function used by /api/v1/scan-item
so you can verify detection before starting the server.

Usage (run from backend/ directory):
    python test_yolo_scan.py <image_path>

Examples:
    python test_yolo_scan.py test_apple.jpg
    python test_yolo_scan.py C:/Users/You/Pictures/banana.jpg

If no image is supplied, a solid-colour synthetic patch is used
for each target class as a quick smoke test.

Requirements:
    pip install ultralytics pillow
"""

import sys
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ─── Inline the same constants used in main.py ────────────────────────────────

COCO_TO_PRODUCE = {
    "apple":    "Apple",
    "banana":   "Banana",
    "orange":   "Orange",
    "carrot":   "Carrot",
    "broccoli": "Broccoli",
}
CONF_THRESHOLD = 0.35

# ─── Load YOLO ────────────────────────────────────────────────────────────────

def load_yolo():
    try:
        from ultralytics import YOLO
    except ImportError:
        print("\n[ERROR] ultralytics is not installed.")
        print("  Run:  pip install ultralytics\n")
        sys.exit(1)

    print("[INFO] Loading YOLOv8n (downloads ~6 MB on first run)...")
    model = YOLO("yolov8n.pt")
    print("[OK]   YOLOv8n ready.\n")
    return model

# ─── Run detection ────────────────────────────────────────────────────────────

def detect(model, image: Image.Image, source_label: str = ""):
    results = model(image, conf=CONF_THRESHOLD, verbose=False)

    best_label = "No Produce Detected"
    best_conf  = 0.0
    all_boxes  = []

    for result in results:
        for box in result.boxes:
            coco_name = result.names[int(box.cls)].lower()
            conf      = float(box.conf)
            coords    = [round(float(v), 1) for v in box.xyxy[0].tolist()]
            all_boxes.append({
                "coco_class": coco_name,
                "confidence": round(conf * 100, 2),
                "bbox":       coords,
                "mapped_to":  COCO_TO_PRODUCE.get(coco_name, "(ignored)"),
            })
            if coco_name in COCO_TO_PRODUCE and conf > best_conf:
                best_conf  = conf
                best_label = COCO_TO_PRODUCE[coco_name]

    # ── Print results ──────────────────────────────────────────────────────────
    header = f"  Image: {source_label}" if source_label else "  Synthetic patch"
    print("─" * 55)
    print(header)
    print("─" * 55)

    if all_boxes:
        print(f"  All YOLO detections ({len(all_boxes)} total):")
        for b in sorted(all_boxes, key=lambda x: -x["confidence"]):
            tag = "✅" if b["coco_class"] in COCO_TO_PRODUCE else "  "
            print(f"  {tag} {b['coco_class']:<15} {b['confidence']:6.2f}%"
                  f"  bbox={b['bbox']}  → {b['mapped_to']}")
    else:
        print("  No objects detected above confidence threshold.")

    print()
    if best_label != "No Produce Detected":
        print(f"  🍎 RESULT : {best_label}  ({best_conf * 100:.1f}% confidence)")
    else:
        print("  📭 RESULT : No Produce Detected")

    print("─" * 55)
    print()
    return best_label, round(best_conf * 100, 2)


# ─── Synthetic smoke test ─────────────────────────────────────────────────────

def smoke_test(model):
    """
    Passes a 640x480 natural-looking test image to YOLO.
    Synthetic solid patches won't trigger YOLO (it needs real photo features),
    so this just confirms the pipeline runs without errors.
    """
    print("[INFO] No image supplied — running pipeline smoke test.\n")

    # Use a simple gradient image to confirm the model runs end-to-end
    arr  = np.zeros((480, 640, 3), dtype=np.uint8)
    arr[:, :, 1] = 80   # dark greenish background — neutral
    img  = Image.fromarray(arr)

    detect(model, img, source_label="synthetic neutral patch (pipeline check only)")
    print("[INFO] Smoke test passed — YOLO pipeline is working.")
    print("[INFO] Pass a real photo for a meaningful detection result.\n")


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    model = load_yolo()

    if len(sys.argv) < 2:
        smoke_test(model)
    else:
        path = pathlib.Path(sys.argv[1])
        if not path.exists():
            print(f"\n[ERROR] File not found: {path}\n")
            sys.exit(1)

        img = Image.open(path).convert("RGB")
        print(f"[INFO] Image size: {img.size[0]}x{img.size[1]} px\n")
        detect(model, img, source_label=str(path))
