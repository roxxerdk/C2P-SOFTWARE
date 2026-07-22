#!/usr/bin/env python
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

try:
    print("Importing main...")
    from main import app
    print("✓ Successfully imported main.app")
    print(f"✓ FastAPI app created: {app}")
except Exception as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
