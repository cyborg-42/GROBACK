from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import io
from PIL import Image
import numpy as np
import tensorflow as tf
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

# Load the pre-trained model (we'll use a simple placeholder for now)
# In a real scenario, you would load a trained Keras model
# model = tf.keras.models.load_model('path/to/model')
# For now, we'll use a dummy model that returns random predictions
def dummy_model_predict(image):
    # This is a placeholder - replace with actual model inference
    # For demonstration, we'll return a fixed set of predictions
    # In reality, you would preprocess the image and run it through your model
    predictions = {
        "Apple": 0.0,
        "Banana": 0.0,
        "Orange": 0.0,
        "Carrot": 0.0
    }
    # Simple color-based mock for demonstration
    img_array = np.array(image)
    # Calculate average color
    avg_color_per_row = np.mean(img_array, axis=0)
    avg_color = np.mean(avg_color_per_row, axis=0)
    r, g, b = avg_color

    # Assign scores based on color
    if r > 150 and g < 100 and b < 100:  # Reddish
        predictions["Apple"] = 0.8 + (r - 150) / 100 * 0.2
    elif r > 130 and g > 130 and b < 100:  # Yellowish
        predictions["Banana"] = 0.7 + (g - 130) / 100 * 0.3
    elif r > 140 and g > 80 and b < 80:   # Orangish
        predictions["Orange"] = 0.75 + (r - 140) / 100 * 0.25
    else:  # Greenish or else
        predictions["Carrot"] = 0.6 + min(g, 100) / 100 * 0.4

    # Normalize to make sure they sum to 1 (approximately)
    total = sum(predictions.values())
    if total > 0:
        predictions = {k: v/total for k, v in predictions.items()}

    return predictions

@app.on_event("startup")
def startup_event():
    database.create_tables()
    print("✅ GroBack Database & Tables Initialized Successfully.")

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

    database.update_quadrant_weight(payload.quadrant, payload.weight_grams)

    await manager.broadcast({
        "type": "WEIGHT_UPDATE",
        "quadrant": payload.quadrant,
        "weight_g": payload.weight_grams
    })

    return {
        "status": "success",
        "quadrant": payload.quadrant,
        "updated_weight_g": payload.weight_grams
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
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        image = image.resize((100, 100))

        # Run model inference (placeholder)
        predictions = dummy_model_predict(image)

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