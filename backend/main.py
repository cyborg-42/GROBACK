"""
main.py
GroBack AI-IoT Smart Shelf — FastAPI Backend
============================================
Vision pipeline: YOLOv8 Nano (pretrained COCO weights)
Weight telemetry: 4-quadrant HX711 load cells via ESP32
Analytics: SQLite + linear regression depletion forecasting
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import io
import numpy as np
from PIL import Image
import database

# ─── YOLOv8 setup ─────────────────────────────────────────────────────────────

try:
    from ultralytics import YOLO
    _yolo_available = True
except ImportError:
    _yolo_available = False
    print("[WARNING] ultralytics not installed. Run: pip install ultralytics")
    print("          Scan endpoint will return fallback response until installed.")

# COCO class names → our shelf produce labels
# Only these 5 classes trigger a positive detection; everything else is ignored.
COCO_TO_PRODUCE = {
    "apple":    "Apple",
    "banana":   "Banana",
    "orange":   "Orange",
    "carrot":   "Carrot",
    "broccoli": "Broccoli",
}

# Minimum YOLO confidence to accept a detection
CONF_THRESHOLD = 0.35

# Lazy-loaded at first request (avoids slow startup on the server)
yolo_model = None

def get_yolo():
    """Load yolov8n.pt on first call, then cache it."""
    global yolo_model
    if yolo_model is None and _yolo_available:
        print("[INFO] Loading YOLOv8n model (downloads ~6 MB on first run)...")
        yolo_model = YOLO("yolov8n.pt")
        print("[SUCCESS] YOLOv8n loaded.")
    return yolo_model


def run_yolo(image: Image.Image):
    """
    Run YOLOv8 on a PIL image and return (label, confidence).

    - Scans all detected bounding boxes.
    - Keeps only boxes whose COCO class maps to a target produce item.
    - Returns the highest-confidence produce detection.
    - Returns ("No Produce Detected", 0.0) when nothing matches.
    """
    model = get_yolo()

    if model is None:
        # ultralytics not installed — return a clearly labelled fallback
        return "No Produce Detected", 0.0

    results = model(image, conf=CONF_THRESHOLD, verbose=False)

    best_label = "No Produce Detected"
    best_conf  = 0.0

    for result in results:
        for box in result.boxes:
            coco_name = result.names[int(box.cls)].lower()
            if coco_name in COCO_TO_PRODUCE:
                conf = float(box.conf)
                if conf > best_conf:
                    best_conf  = conf
                    best_label = COCO_TO_PRODUCE[coco_name]

    return best_label, round(best_conf * 100, 2)


# ─── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="GroBack AI-IoT Backend API",
    version="2.0.0",
    description="Smart shelf backend — YOLOv8 produce detection + HX711 weight telemetry",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket connection manager ─────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ─── Pydantic request models ───────────────────────────────────────────────────

class WeightUpdatePayload(BaseModel):
    quadrant: int
    weight_grams: float

class SimulateScanPayload(BaseModel):
    label: str
    confidence: float


# ─── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup_event():
    database.create_tables()
    print("[SUCCESS] GroBack database initialised.")
    # Pre-warm YOLO so the first scan isn't slow
    if _yolo_available:
        get_yolo()


# ─── Core endpoints ───────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status":  "Online",
        "system":  "GroBack AI-IoT Smart Shelf Backend",
        "version": "2.0.0",
        "vision":  "YOLOv8n (COCO pretrained)",
        "endpoints": [
            "/api/v1/scan-item",
            "/api/v1/inventory",
            "/api/v1/scans",
            "/api/v1/depletion-analytics",
            "/api/v1/update-weight",
            "/api/v1/simulate-scan",
        ],
    }

@app.get("/health")
def health_check():
    return {
        "status":       "healthy",
        "yolo_ready":   yolo_model is not None,
        "yolo_available": _yolo_available,
    }


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()   # keep-alive; we only push from server
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── Inventory & analytics ────────────────────────────────────────────────────

@app.get("/api/v1/inventory")
def get_inventory():
    return database.get_all_inventory()

@app.get("/api/v1/inventory/summary")
def get_inventory_summary():
    return database.get_inventory_summary()

@app.get("/api/v1/scans")
def get_recent_scans():
    return database.get_recent_scans()

@app.get("/api/v1/depletion-analytics")
def get_depletion_analytics():
    return database.get_depletion_analytics()


# ─── Weight telemetry (ESP32 HX711) ───────────────────────────────────────────

@app.post("/api/v1/update-weight")
async def update_weight(payload: WeightUpdatePayload):
    if payload.quadrant not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Quadrant must be 1–4")

    result    = database.update_quadrant_weight(payload.quadrant, payload.weight_grams)
    status    = result["status"]
    item_name = result["item_name"]

    # Standard weight update — all clients refresh inventory
    await manager.broadcast({
        "type":      "WEIGHT_UPDATE",
        "quadrant":  payload.quadrant,
        "weight_g":  payload.weight_grams,
        "status":    status,
        "item_name": item_name,
    })

    # Dedicated depletion alert when weight hits zero
    if status == "Depleted":
        await manager.broadcast({
            "type":      "STOCK_DEPLETED",
            "quadrant":  payload.quadrant,
            "item_name": item_name,
            "message":   f"{item_name} in Quadrant {payload.quadrant} is fully depleted. Please restock.",
        })

    return {
        "status":           "success",
        "quadrant":         payload.quadrant,
        "updated_weight_g": payload.weight_grams,
        "stock_status":     status,
        "item_name":        item_name,
    }


# ─── Simulate scan (testing / demo) ───────────────────────────────────────────

@app.post("/api/v1/simulate-scan")
async def simulate_scan(payload: SimulateScanPayload):
    database.log_scan_result(payload.label, payload.confidence)

    await manager.broadcast({
        "type":       "SCAN_UPDATE",
        "label":      payload.label,
        "confidence": payload.confidence,
    })

    return {
        "status":        "success",
        "detected_item": payload.label,
        "confidence":    payload.confidence,
    }


# ─── YOLOv8 scan endpoint ──────────────────────────────────────────────────────

@app.post("/api/v1/scan-item")
async def scan_item(file: UploadFile = File(...)):
    """
    Accepts a JPEG/PNG image from the phone camera or ESP32-CAM.

    Processing pipeline:
      1. Decode uploaded bytes → PIL Image (RGB)
      2. Pass to YOLOv8n with conf=0.35
      3. Filter detections to COCO produce classes only
      4. Return highest-confidence produce label, or "No Produce Detected"
      5. Log to SQLite and broadcast over WebSocket

    Response: {"success": true, "detected_item": "Banana", "confidence": "94.2%"}
    """
    try:
        contents = await file.read()
        image    = Image.open(io.BytesIO(contents)).convert("RGB")

        label, confidence = run_yolo(image)

        # Always log (including "No Produce Detected" so the scan history is honest)
        database.log_scan_result(label, confidence)

        # Broadcast to all connected Flutter clients
        await manager.broadcast({
            "type":       "SCAN_UPDATE",
            "label":      label,
            "confidence": confidence,
        })

        return {
            "success":       True,
            "detected_item": label,
            "confidence":    f"{confidence:.1f}%",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
