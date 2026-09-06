import urllib.request, json, io
from PIL import Image

BASE = "http://127.0.0.1:8000"

img  = Image.new("RGB", (640, 480), color=(220, 200, 50))
buf  = io.BytesIO()
img.save(buf, format="JPEG")
jpeg = buf.getvalue()

boundary = b"testboundary"
body  = b"--" + boundary + b"\r\n"
body += b'Content-Disposition: form-data; name="file"; filename="test.jpg"\r\n'
body += b"Content-Type: image/jpeg\r\n\r\n"
body += jpeg + b"\r\n"
body += b"--" + boundary + b"--\r\n"

req = urllib.request.Request(
    BASE + "/api/v1/scan-item", data=body,
    headers={"Content-Type": "multipart/form-data; boundary=" + boundary.decode()},
    method="POST",
)
try:
    r    = urllib.request.urlopen(req, timeout=30)
    resp = json.loads(r.read())
    print("[PASS] scan-item returned 200")
    print(f"       detected_item : {resp['detected_item']}")
    print(f"       confidence    : {resp['confidence']}")
    print(f"       pending_bind  : {resp['pending_bind']}")
except urllib.error.HTTPError as e:
    print(f"[FAIL] HTTP {e.code}: {e.read()}")
except Exception as ex:
    print(f"[FAIL] {ex}")
