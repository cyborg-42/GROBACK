from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import io
import os
from PIL import Image
import numpy as np
try:
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
except ImportError:
    tf = None
    mobilenet_preprocess = None
import database

app = FastAPI(title="GroBack AI-IoT Backend API", version="1.0.0")

# Enable CORS for Flutter web, mobile & emulator clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSockets Connection Manager
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
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

class WeightUpdatePayload(BaseModel):
    quadrant: int
    weight_grams: float

class SimulateScanPayload(BaseModel):
    label: str
    confidence: float

# Class labels — alphabetical, must match train_mobilenet.py CLASSES exactly
CLASSES = ["Banana", "Empty"]

# Input size — must match train_mobilenet.py IMG_SIZE
IMG_SIZE = 128

MODEL_PATH = "models/model.h5"

# Load the pre-trained CNN model
model = None

def load_model():
    global model
    if tf is None:
        print("TensorFlow not available, using color-based fallback model")
        return
    try:
        import os
        if os.path.exists(MODEL_PATH):
            model = tf.keras.models.load_model(MODEL_PATH)
            actual_size = model.input_shape[1]
            print(f"[SUCCESS] CNN model loaded from {MODEL_PATH} (input: {actual_size}×{actual_size})")
            # Override IMG_SIZE globally so model_predict uses the right resolution
            global IMG_SIZE
            IMG_SIZE = actual_size
        else:
            print(f"[WARNING] Model file not found at {MODEL_PATH}, using color-based fallback")
            model = None
    except Exception as e:
        print(f"[WARNING] Failed to load CNN model: {e}")
        print("   Falling back to color-based model")
        model = None

def model_predict(image):
    """
    Run inference on a PIL Image.
    Preprocessing matches train_mobilenet.py exactly:
      - Resize to IMG_SIZE x IMG_SIZE (128x128)
      - MobileNetV2 preprocess_input scales pixels to [-1, 1]
    Falls back to colour heuristic if no model is loaded.
    Uses the model's actual output size so old and new checkpoints both work.
    """
    if model is not None:
        img_array = np.array(image.resize((IMG_SIZE, IMG_SIZE)), dtype=np.float32)
        img_array = mobilenet_preprocess(img_array)
        img_array = np.expand_dims(img_array, axis=0)
        predictions = model.predict(img_array, verbose=0)[0]
        # Use model output length in case checkpoint has different num classes
        n = min(len(predictions), len(CLASSES))
        return {CLASSES[i]: float(predictions[i]) for i in range(n)}
    else:
        return dummy_model_predict(image)


def dummy_model_predict(image):
    """
    Colour-based fallback when no model is loaded.
    Bananas are yellow (high R+G, low B) — everything else is Empty shelf.
    """
    img_array = np.array(image.resize((IMG_SIZE, IMG_SIZE)))
    avg = np.mean(img_array.reshape(-1, 3), axis=0)
    r, g, b = avg

    # Yellow heuristic: high red + high green, low blue
    banana_score = 0.0
    if r > 150 and g > 130 and b < 120:
        banana_score = min(0.5 + (g - 130) / 200, 0.95)

    empty_score = 1.0 - banana_score
    return {"Banana": banana_score, "Empty": empty_score}

@app.on_event("startup")
def startup_event():
    database.create_tables()
    load_model()  # Load the trained model
    print("[SUCCESS] GroBack Database & Tables Initialized Successfully.")

@app.get("/")
def root():
    return {
        "status": "Online",
        "system": "GroBack AI-IoT Smart Shelf Backend",
        "version": "1.0.0",
        "endpoints": [
            "/api/v1/inventory",
            "/api/v1/scans",
            "/api/v1/depletion-analytics",
            "/api/v1/update-weight",
            "/api/v1/simulate-scan",
            "/api/v1/scan-item",
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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

@app.post("/api/v1/update-weight")
async def update_weight(payload: WeightUpdatePayload):
    if payload.quadrant not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Quadrant must be between 1 and 4")

    # Capture status and item_name returned by the DB layer
    result = database.update_quadrant_weight(payload.quadrant, payload.weight_grams)
    status    = result["status"]
    item_name = result["item_name"]

    # Always broadcast the standard weight update (all connected clients refresh)
    await manager.broadcast({
        "type":      "WEIGHT_UPDATE",
        "quadrant":  payload.quadrant,
        "weight_g":  payload.weight_grams,
        "status":    status,
        "item_name": item_name,
    })

    # When a quadrant hits zero, fire a dedicated depletion alert
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

@app.post("/api/v1/simulate-scan")
async def simulate_scan(payload: SimulateScanPayload):
    database.log_scan_result(payload.label, payload.confidence)

    await manager.broadcast({
        "type": "SCAN_UPDATE",
        "label": payload.label,
        "confidence": payload.confidence
    })

    return {
        "status": "success",
        "detected_item": payload.label,
        "confidence": payload.confidence
    }

@app.post("/api/v1/scan-item")
async def scan_item(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        # Decode image — resize is handled inside model_predict to IMG_SIZE
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Run model inference (preprocessing matched to training pipeline)
        predictions = model_predict(image)

        # Get the top prediction
        label = max(predictions, key=predictions.get)
        confidence = predictions[label] * 100  # Convert to percentage

        # Log the scan result
        database.log_scan_result(label, confidence)

        # Broadcast to websocket clients
        await manager.broadcast({
            "type": "SCAN_UPDATE",
            "label": label,
            "confidence": confidence
        })

        return {
            "success": True,
            "detected_item": label,
            "confidence": f"{confidence:.1f}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))