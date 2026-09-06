"""
smoke_test.py  — run from backend/ while server is running
Tests every endpoint in sequence and prints pass/fail.
"""
import urllib.request
import json
import time
import os

BASE = "http://127.0.0.1:8000"

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

results = []

def get(path):
    r = urllib.request.urlopen(f"{BASE}{path}", timeout=5)
    return json.loads(r.read()), r.status

def post(path, data=None, files=None):
    if files:
        # multipart upload
        import io, mimetypes
        boundary = b"grobackboundary"
        body = b""
        for name, (fname, fdata, ctype) in files.items():
            body += b"--" + boundary + b"\r\n"
            body += f'Content-Disposition: form-data; name="{name}"; filename="{fname}"\r\n'.encode()
            body += f"Content-Type: {ctype}\r\n\r\n".encode()
            body += fdata + b"\r\n"
        body += b"--" + boundary + b"--\r\n"
        req = urllib.request.Request(
            f"{BASE}{path}", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary.decode()}"},
            method="POST"
        )
    else:
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{BASE}{path}", data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
    try:
        r = urllib.request.urlopen(req, timeout=30)   # 30s for YOLO on CPU
        return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def check(name, condition, detail=""):
    tag = PASS if condition else FAIL
    msg = f"{tag} {name}"
    if detail:
        msg += f"  →  {detail}"
    print(msg)
    results.append((name, condition))
    return condition

print("=" * 60)
print("  GroBack Backend Smoke Test")
print("=" * 60)

# ── 1. Health ─────────────────────────────────────────────────
print("\n[1] Health check")
r, code = get("/health")
check("GET /health returns 200", code == 200)
check("yolo_available is True", r.get("yolo_available") is True, str(r))
check("yolo_ready is True", r.get("yolo_ready") is True, str(r))

# ── 2. Root ───────────────────────────────────────────────────
print("\n[2] Root endpoint")
r, code = get("/")
check("GET / returns 200", code == 200)
check("version is 2.0.0", r.get("version") == "2.0.0", r.get("version"))
check("/api/v1/pending-scan listed", "/api/v1/pending-scan" in r.get("endpoints", []))

# ── 3. Inventory ──────────────────────────────────────────────
print("\n[3] Inventory")
r, code = get("/api/v1/inventory")
check("GET /api/v1/inventory returns 200", code == 200)
check("Returns 4 quadrants", len(r) == 4, f"got {len(r)}")
names = [i["item_name"] for i in r]
check("All 4 COCO classes present", sorted(names) == ["Apple","Banana","Carrot","Orange"], str(names))

# ── 4. Inventory summary ──────────────────────────────────────
print("\n[4] Inventory summary")
r, code = get("/api/v1/inventory/summary")
check("GET /api/v1/inventory/summary returns 200", code == 200)
check("Has total_items", "total_items" in r, str(r))

# ── 5. Depletion analytics ────────────────────────────────────
print("\n[5] Depletion analytics")
r, code = get("/api/v1/depletion-analytics")
check("GET /api/v1/depletion-analytics returns 200", code == 200)
check("Returns 4 metrics", len(r) == 4, f"got {len(r)}")
check("Has estimated_days_remaining", "estimated_days_remaining" in r[0], str(r[0]))

# ── 6. Pending scan (empty) ───────────────────────────────────
print("\n[6] Pending scan buffer (should be empty)")
r, code = get("/api/v1/pending-scan")
check("GET /api/v1/pending-scan returns 200", code == 200)
check("pending is False initially", r.get("pending") is False, str(r))
check("item is None", r.get("item") is None, str(r))

# ── 7. Weight update — normal consumption ────────────────────
print("\n[7] Weight update (consumption, no pending scan)")
r, code = post("/api/v1/update-weight", {"quadrant": 1, "weight_grams": 300.0})
check("POST /api/v1/update-weight returns 200", code == 200, str(r))
check("stock_status present", "stock_status" in r, str(r))
check("item_name present", "item_name" in r, str(r))
check("delta_g present", "delta_g" in r, str(r))
check("binding key absent (no pending scan)", "binding" not in r, str(r))

# ── 8. Weight update — invalid quadrant ──────────────────────
print("\n[8] Weight update — invalid quadrant (expect 400)")
r, code = post("/api/v1/update-weight", {"quadrant": 5, "weight_grams": 100.0})
check("Returns 400 for quadrant=5", code == 400, f"got {code}")

# ── 9. Simulate scan ──────────────────────────────────────────
print("\n[9] Simulate scan")
r, code = post("/api/v1/simulate-scan", {"label": "Banana", "confidence": 92.0})
check("POST /api/v1/simulate-scan returns 200", code == 200, str(r))
check("detected_item matches", r.get("detected_item") == "Banana", str(r))

# ── 10. Recent scans ──────────────────────────────────────────
print("\n[10] Recent scans")
r, code = get("/api/v1/scans")
check("GET /api/v1/scans returns 200", code == 200)
check("Has at least 1 scan entry", len(r) >= 1, f"got {len(r)}")
check("Scan has label field", "label" in r[0], str(r[0]))

# ── 11. Scan-item endpoint (synthetic image) ──────────────────
print("\n[11] POST /api/v1/scan-item (solid yellow patch)")
from PIL import Image
import io as _io
# Solid yellow 640x480 image — YOLO won't detect a real banana here
# but the endpoint must handle it without crashing
img = Image.new("RGB", (640, 480), color=(220, 200, 50))
buf = _io.BytesIO()
img.save(buf, format="JPEG")
jpeg_bytes = buf.getvalue()

r, code = post("/api/v1/scan-item", files={
    "file": ("test.jpg", jpeg_bytes, "image/jpeg")
})
check("POST /api/v1/scan-item returns 200", code == 200, str(r))
check("detected_item field present", "detected_item" in r, str(r))
check("confidence field present", "confidence" in r, str(r))
check("success is True", r.get("success") is True, str(r))
check("pending_bind field present", "pending_bind" in r, str(r))
print(f"  {INFO} YOLO result on yellow patch: {r.get('detected_item')} {r.get('confidence')}")

# ── 12. Delta-binding end-to-end ──────────────────────────────
print("\n[12] Delta-binding: scan then place on shelf")

# Step 1 — fake a successful scan to populate pending_scan
# Use simulate-scan so we don't need a real image but also manually
# set pending via the actual scan-item endpoint with a real banana image
# For now test via simulate-scan + check pending remains empty (it won't
# set pending — only scan-item does), then test the binding path directly.

# First check pending is currently clear
r, code = get("/api/v1/pending-scan")
check("Pending clear before binding test", r.get("pending") is False, str(r))

# Now post a weight increase > 30g — with no pending scan it should NOT bind
r, code = post("/api/v1/update-weight", {"quadrant": 2, "weight_grams": 500.0})
check("Weight update without pending: no binding", "binding" not in r, str(r))
check("item_name unchanged (Banana)", r.get("item_name") == "Banana", str(r))

# ── Summary ───────────────────────────────────────────────────
print()
print("=" * 60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total  = len(results)
print(f"  Results: {passed}/{total} passed  |  {failed} failed")
print("=" * 60)

if failed > 0:
    print("\n  Failed checks:")
    for name, ok in results:
        if not ok:
            print(f"    ✗ {name}")
