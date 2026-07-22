import sys
import json
from pathlib import Path
import httpx

image_path = Path("../dataset/drawings/test_image.png")

if not image_path.exists():
    print(f"❌ File not found at: {image_path.resolve()}")
    sys.exit(1)

print("🚀 Testing C2P FastAPI Endpoint...\n")

url = "http://127.0.0.1:8000/run-pipeline"

try:
    with open(image_path, "rb") as f:
        files = {"file": ("test_image.png", f, "image/png")}
        
        with httpx.stream("POST", url, files=files, timeout=None) as response:
            print(f"📡 Connected! HTTP Status: {response.status_code}")
            print("=" * 60)
            
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith(": keep-alive"):
                    print("⏳ [SERVER] Processing in background (keep-alive)...")
                    sys.stdout.flush()
                elif line.startswith("data: "):
                    try:
                        payload = json.loads(line[6:])
                        stage = payload.get("stage", "unknown")
                        status = payload.get("status", "ok")
                        
                        if stage == "error":
                            print(f"\n❌ [PIPELINE ERROR DETAIL]: {payload.get('error')}")
                        else:
                            print(f"⚡ [SSE EVENT] Stage: {stage.upper()} | Status: {status}")
                        sys.stdout.flush()
                    except Exception:
                        print(f"📡 [RAW DATA] {line}")
                        sys.stdout.flush()

except Exception as e:
    print(f"\n❌ Request failed: {e}")