import sqlite3
from datetime import datetime, timedelta
import json
import numpy as np
from typing import List, Dict, Any, Optional

DATABASE_NAME = "grocery.db"

def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Drop old incompatible schema if quadrant column is missing
    cursor.execute("PRAGMA table_info(inventory)")
    columns = [row[1] for row in cursor.fetchall()]
    if columns and "quadrant" not in columns:
        cursor.execute("DROP TABLE inventory")

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
    return [dict(row) for row in rows]

def get_inventory_summary():
    """Returns a quick summary: total items, critical count, low stock count."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM inventory")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE status = 'Critical'")
    critical = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE status = 'Low Stock'")
    low_stock = cursor.fetchone()[0]
    conn.close()
    return {"total_items": total, "critical": critical, "low_stock": low_stock}

def get_depletion_analytics():
    inventory = get_all_inventory()
    metrics = []

    for item in inventory:
        name = item['item_name']
        current_w = item['weight_g']
        quadrant = item['quadrant']

        # Get recent weight logs for this quadrant to compute depletion rate via linear regression
        conn = get_connection()
        cursor = conn.cursor()
        # Get last 20 weight logs for this quadrant, ordered by timestamp (oldest first for regression)
        cursor.execute("""
            SELECT weight_g, timestamp FROM weight_logs
            WHERE quadrant = ?
            ORDER BY timestamp ASC
            LIMIT 20
        """, (quadrant,))
        logs = cursor.fetchall()
        conn.close()

        # If we have sufficient data points, compute linear regression
        if len(logs) >= 3:
            try:
                # Convert timestamps to seconds since epoch for linear regression
                times = []
                weights = []
                for log in logs:
                    weight_g = log[0]
                    timestamp_str = log[1]
                    # Parse SQLite timestamp format: "YYYY-MM-DD HH:MM:SS"
                    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    # Convert to seconds since epoch
                    timestamp_seconds = dt.timestamp()
                    times.append(timestamp_seconds)
                    weights.append(weight_g)

                # Perform linear regression: weight = slope * time + intercept
                # Slope is the rate of weight change per second
                n = len(times)
                sum_x = sum(times)
                sum_y = sum(weights)
                sum_xy = sum(t * w for t, w in zip(times, weights))
                sum_x2 = sum(t * t for t in times)

                # Calculate slope (rate of change per second)
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

                # Convert slope to grams per day (negative slope means depletion)
                # slope is in grams/second, convert to grams/day: * 60 * 60 * 24
                daily_rate_g = -slope * 86400  # Negative because we want depletion rate as positive

                # Ensure rate is reasonable (between 0 and 500g/day)
                if daily_rate_g < 0:
                    daily_rate_g = 0  # Weight increasing (shouldn't happen in depletion)
                elif daily_rate_g > 500:
                    daily_rate_g = 500  # Cap at reasonable maximum

            except Exception as e:
                # Fallback to fixed rates if regression fails
                print(f"Linear regression failed for {name}: {e}")
                daily_rate_g = get_fallback_rate(name)
        else:
            # Not enough data points, use fallback rate
            daily_rate_g = get_fallback_rate(name)

        # Calculate estimated days remaining
        if daily_rate_g > 0:
            days_left = round(current_w / daily_rate_g, 1)
        else:
            days_left = 99.0  # Essentially infinite if no depletion

        metrics.append({
            "item_name": name,
            "quadrant": item['quadrant'],
            "current_weight_g": current_w,
            "daily_rate_g": round(daily_rate_g, 2),
            "estimated_days_remaining": days_left,
            "stock_status": item['status'],
        })

    return metrics


def get_fallback_rate(item_name: str) -> float:
    """Provide fallback depletion rates when insufficient data for linear regression."""
    fallback_rates = {
        "Apple": 120.0,
        "Banana": 150.0,
        "Orange": 140.0,
        "Carrot": 100.0,
    }
    return fallback_rates.get(item_name, 110.0)