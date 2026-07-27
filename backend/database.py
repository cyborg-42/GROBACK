import sqlite3
from datetime import datetime

DATABASE_NAME = "grocery.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Inventory state per 4-Quadrant tray
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quadrant INTEGER UNIQUE NOT NULL,
        item_name TEXT NOT NULL,
        weight_g REAL NOT NULL,
        max_capacity_g REAL DEFAULT 1000.0,
        status TEXT DEFAULT 'Available',
        last_updated TEXT
    )
    """)

    # Telemetry weight logs from HX711 38-Pin ESP32
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weight_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quadrant INTEGER NOT NULL,
        weight_g REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Camera scan logs from ESP32-CAM
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        confidence REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Seed initial 4 Quadrants if empty
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        seed_data = [
            (1, "Apple", 450.0, 1000.0, "Available", "Just now"),
            (2, "Banana", 180.0, 1000.0, "Low Stock", "5 mins ago"),
            (3, "Orange", 620.0, 1000.0, "Available", "10 mins ago"),
            (4, "Carrot", 80.0, 1000.0, "Critical", "15 mins ago"),
        ]
        cursor.executemany(
            "INSERT INTO inventory (quadrant, item_name, weight_g, max_capacity_g, status, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
            seed_data
        )

    conn.commit()
    conn.close()

def get_all_inventory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory ORDER BY quadrant ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_quadrant_weight(quadrant: int, weight_g: float):
    conn = get_connection()
    cursor = conn.cursor()
    
    status = "Available"
    if weight_g < 100:
        status = "Critical"
    elif weight_g < 250:
        status = "Low Stock"

    now_str = datetime.now().strftime("%I:%M %p")
    cursor.execute(
        "UPDATE inventory SET weight_g = ?, status = ?, last_updated = ? WHERE quadrant = ?",
        (weight_g, status, now_str, quadrant)
    )
    cursor.execute(
        "INSERT INTO weight_logs (quadrant, weight_g) VALUES (?, ?)",
        (quadrant, weight_g)
    )
    conn.commit()
    conn.close()

def log_scan_result(label: str, confidence: float):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%I:%M %p")
    cursor.execute(
        "INSERT INTO scan_logs (label, confidence, timestamp) VALUES (?, ?, ?)",
        (label, confidence, now_str)
    )
    conn.commit()
    conn.close()

def get_recent_scans(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scan_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return [
            {"id": 1, "label": "Apple", "confidence": 96.4, "timestamp": "10:30 AM"},
            {"id": 2, "label": "Orange", "confidence": 92.1, "timestamp": "10:15 AM"},
            {"id": 3, "label": "Banana", "confidence": 88.7, "timestamp": "09:45 AM"},
        ]
    return [dict(row) for row in rows]

def get_depletion_analytics():
    inventory = get_all_inventory()
    rates = {
        "Apple": 120.0,
        "Banana": 150.0,
        "Orange": 140.0,
        "Carrot": 100.0,
    }
    metrics = []
    for item in inventory:
        name = item['item_name']
        current_w = item['weight_g']
        daily_rate = rates.get(name, 110.0)
        days_left = round(current_w / daily_rate, 1) if daily_rate > 0 else 99.0
        
        metrics.append({
            "item_name": name,
            "quadrant": item['quadrant'],
            "current_weight_g": current_w,
            "daily_rate_g": daily_rate,
            "estimated_days_remaining": days_left,
            "stock_status": item['status'],
        })
    return metrics
