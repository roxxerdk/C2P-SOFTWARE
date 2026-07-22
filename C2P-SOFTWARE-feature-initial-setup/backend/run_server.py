#!/usr/bin/env python
import sys
import os

# Add backend directory to Python path
backend_dir = r"c:\Users\pragn.LAPTOP-DAHFBVDA\Downloads\C2P-SOFTWARE-feature-initial-setup\C2P-SOFTWARE-feature-initial-setup\backend"
sys.path.insert(0, backend_dir)

# Change working directory
os.chdir(backend_dir)

# Import and run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
