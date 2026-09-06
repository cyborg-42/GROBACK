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
import asyncio
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


def _run_yolo_sync(image: Image.Image):
    """
    Synchronous YOLO inference — runs in a thread pool via asyncio.
    Converts PIL Image to numpy array (what ultralytics actually expects).
    Returns (label, confidence_percent).
    """
    model = get_yolo()
    if model is None:
        return "No Produce Detected", 0.0

    # Convert PIL → numpy RGB array (HxWx3 uint8) — ultralytics native format
    img_array = np.array(image)

    results = model(img_array, conf=CONF_THRESHOLD, verbose=False)

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


async def run_yolo(image: Image.Image):
    """
    Async wrapper: offloads CPU-bound YOLO inference to a thread pool
    so the FastAPI event loop is never blocked.
    Other requests (weight updates, WebSocket pings) remain responsive
    during a scan even on slow CPU hardware.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _run_yolo_sync, image)


# ─── Delta-binding: pending scan buffer ───────────────────────────────────────
# Lifecycle:
#   Step 1 — User scans produce at the camera station → pending_scan is set
#   Step 2 — User places produce on a tray → ESP32 posts a weight increase
#   Step 3 — update-weight detects ΔW > 30g and pending_scan is set
#            → auto-binds the scanned item to that quadrant
#
# The buffer expires after PENDING_SCAN_TTL_SECONDS to prevent a stale scan
# from incorrectly binding to a weight change that happens much later.

import time as _time

PENDING_SCAN_TTL_SECONDS = 30   # scan must be placed within 30 s

pending_scan: dict = {
    "item":       None,    # e.g. "Banana"
    "confidence": 0.0,
    "timestamp":  None,    # _time.time() float
}

def _clear_pending():
    pending_scan["item"]       = None
    pending_scan["confidence"] = 0.0
    pending_scan["timestamp"]  = None

def _pending_is_valid() -> bool:
    """True if a scan is waiting and hasn't expired yet."""
    if pending_scan["item"] is None:
        return False
    age = _time.time() - (pending_scan["timestamp"] or 0)
    return age <= PENDING_SCAN_TTL_SECONDS


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
            "/api/v1/pending-scan",
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


# ─── Weight telemetry (ESP32 HX711) + delta-binding ──────────────────────────

# Minimum positive weight delta (grams) to treat as a new item placement.
# Filters out sensor noise and vibration.
DELTA_THRESHOLD_ADD    =  30.0   # +30 g → item placed
DELTA_THRESHOLD_REMOVE = -10.0   # -10 g → consumption / removal

@app.post("/api/v1/update-weight")
async def update_weight(payload: WeightUpdatePayload):
    """
    Receives weight telemetry from the ESP32 HX711 sensors.

    Delta-binding algorithm:
      Case 1 — ΔW > +30g AND pending scan exists (TTL valid)
               → auto-bind scanned item to this quadrant
      Case 2 — ΔW > +30g but NO pending scan
               → weight increased without a scan (manual placement or error)
                 just update the weight, keep existing item_name
      Case 3 — ΔW < -10g
               → consumption detected, update weight only

    All cases broadcast WEIGHT_UPDATE. Case 1 also broadcasts ITEM_BOUND.
    Zero weight broadcasts STOCK_DEPLETED.
    """
    if payload.quadrant not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Quadrant must be 1–4")

    # Read current state before updating
    current = database.get_quadrant(payload.quadrant)
    current_weight = current.get("weight_g", 0.0)
    delta = payload.weight_grams - current_weight

    bound_item = None  # set if delta-binding fires

    # ── Case 1: item placed after a scan ──────────────────────────────────────
    if delta >= DELTA_THRESHOLD_ADD and _pending_is_valid():
        bound_item = pending_scan["item"]
        scan_conf  = pending_scan["confidence"]
        result     = database.update_quadrant_item(
            payload.quadrant, bound_item, payload.weight_grams
        )
        _clear_pending()

        print(f"[BIND] 🎯 Auto-bound '{bound_item}' → Quadrant {payload.quadrant} "
              f"(ΔW={delta:+.0f}g, scan conf={scan_conf:.1f}%)")

        # Notify Flutter: item identity changed
        await manager.broadcast({
            "type":       "ITEM_BOUND",
            "quadrant":   payload.quadrant,
            "item_name":  bound_item,
            "weight_g":   payload.weight_grams,
            "confidence": scan_conf,
            "message":    f"{bound_item} placed on Quadrant {payload.quadrant}",
        })

    # ── Case 2 & 3: weight-only update ────────────────────────────────────────
    else:
        result = database.update_quadrant_weight(payload.quadrant, payload.weight_grams)
        if delta >= DELTA_THRESHOLD_ADD:
            print(f"[WEIGHT] Q{payload.quadrant} +{delta:.0f}g (no pending scan — "
                  f"keeping item '{result['item_name']}')")
        elif delta <= DELTA_THRESHOLD_REMOVE:
            print(f"[WEIGHT] Q{payload.quadrant} {delta:.0f}g consumption detected")

    status    = result["status"]
    item_name = result["item_name"]

    # Always broadcast the weight update so inventory UI refreshes
    await manager.broadcast({
        "type":      "WEIGHT_UPDATE",
        "quadrant":  payload.quadrant,
        "weight_g":  payload.weight_grams,
        "status":    status,
        "item_name": item_name,
    })

    # Depletion alert when weight hits exactly zero
    if status == "Depleted":
        await manager.broadcast({
            "type":      "STOCK_DEPLETED",
            "quadrant":  payload.quadrant,
            "item_name": item_name,
            "message":   f"{item_name} in Quadrant {payload.quadrant} is fully depleted. Please restock.",
        })

    response = {
        "status":           "success",
        "quadrant":         payload.quadrant,
        "updated_weight_g": payload.weight_grams,
        "delta_g":          round(delta, 1),
        "stock_status":     status,
        "item_name":        item_name,
    }
    if bound_item:
        response["bound_item"] = bound_item
        response["binding"]    = "auto"

    return response


# ─── Pending scan status (for Flutter UI) ─────────────────────────────────────

@app.get("/api/v1/pending-scan")
def get_pending_scan():
    """
    Returns the current pending scan buffer state.
    Flutter can poll this to show a 'Place on shelf now' prompt.
    """
    if _pending_is_valid():
        age = round(_time.time() - pending_scan["timestamp"], 1)
        return {
            "pending":    True,
            "item":       pending_scan["item"],
            "confidence": pending_scan["confidence"],
            "age_seconds": age,
            "ttl_seconds": PENDING_SCAN_TTL_SECONDS,
            "expires_in":  round(PENDING_SCAN_TTL_SECONDS - age, 1),
        }
    return {"pending": False, "item": None}


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

    Pipeline:
      1. Decode image → YOLOv8n (conf=0.35)
      2. If produce detected → store in pending_scan buffer (TTL 30 s)
         The next weight increase >30 g on any quadrant auto-binds it.
      3. Log + broadcast SCAN_UPDATE regardless of detection result.

    Response: {"success": true, "detected_item": "Banana", "confidence": "94.2%"}
    """
    try:
        contents = await file.read()
        image    = Image.open(io.BytesIO(contents)).convert("RGB")

        label, confidence = await run_yolo(image)

        # Set pending buffer so update-weight can bind this item to a quadrant
        if label != "No Produce Detected":
            pending_scan["item"]       = label
            pending_scan["confidence"] = confidence
            pending_scan["timestamp"]  = _time.time()
            print(f"[SCAN] Detected {label} ({confidence:.1f}%) — "
                  f"waiting for shelf placement (TTL {PENDING_SCAN_TTL_SECONDS}s)")
        else:
            # No produce found — clear any stale pending entry
            _clear_pending()

        database.log_scan_result(label, confidence)

        await manager.broadcast({
            "type":       "SCAN_UPDATE",
            "label":      label,
            "confidence": confidence,
        })

        return {
            "success":        True,
            "detected_item":  label,
            "confidence":     f"{confidence:.1f}%",
            "pending_bind":   label != "No Produce Detected",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
