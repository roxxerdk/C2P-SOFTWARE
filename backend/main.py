import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="C2P AI Copilot Backend", version="0.1.0")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load drawings catalog data
CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "drawings", "drawings_catalog.json")

def load_catalog():
    if os.path.exists(CATALOG_PATH):
        with open(CATALOG_PATH, "r") as f:
            return json.load(f)
    return []

@app.get("/")
def read_root():
    return {"message": "Welcome to the C2P AI Copilot Backend Service"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "c2p-backend"}

@app.get("/drawings")
def get_drawings():
    """Get the list of pre-configured drawings in the dataset catalog."""
    return load_catalog()

# Endpoint for uploading drawing image and processing it
@app.post("/upload")
async def upload_drawing(file: UploadFile = File(...)):
    """
    Accepts drawing image files, performs simulated preprocessing,
    and runs the Planning & Drawing Understanding Agents to output structured JSON.
    """
    # 1. Simulate Image Preprocessing
    # We read file parameters
    filename = file.filename
    content_type = file.content_type
    
    # 2. Check if the file matches one of our catalog drawings by name
    catalog = load_catalog()
    matched_drawing = None
    
    # Clean the filename for matching
    clean_name = filename.lower().split(".")[0].replace("_", " ").replace("-", " ")
    for drawing in catalog:
        if drawing["name"].lower() in clean_name or drawing["id"].lower() in clean_name:
            matched_drawing = drawing
            break
            
    # 3. If no direct catalog match, generate a dynamic mock structure based on name/category guess
    if not matched_drawing:
        # Default fallback drawing structure
        category = "Plate"
        if "shaft" in clean_name:
            category = "Shaft"
        elif "bracket" in clean_name:
            category = "Bracket"
        elif "flange" in clean_name:
            category = "Flange"
        elif "block" in clean_name:
            category = "Block"
            
        matched_drawing = {
            "id": f"dr_dynamic_{int(len(catalog) + 1)}",
            "name": filename.split(".")[0].replace("_", " ").title(),
            "category": category,
            "material": "Aluminium" if category in ["Plate", "Block"] else "Steel",
            "dimensions": "100x80x20" if category != "Shaft" else "OD25 x 150",
            "features": [
              {"id": "feat_1", "name": "Through Hole", "details": "Dia 10.0mm standard hole", "balloon": 1},
              {"id": "feat_2", "name": "Pocket", "details": "Recessed cavity", "balloon": 2},
              {"id": "feat_3", "name": "Chamfer", "details": "2mm edge break", "balloon": 3}
            ]
        }
        
    # Return structured metadata simulating Planning Agent and Drawing Understanding output
    return {
        "preprocessing_status": "Success",
        "preprocessing_logs": [
            "Grayscale conversion completed.",
            "Binarization and adaptive thresholding applied.",
            "Noise reduction (Gaussian Blur) completed.",
            "Edge lines and boundary alignment corrected."
        ],
        "planning_agent": {
            "classification": matched_drawing["category"],
            "confidence_score": 0.98,
            "detected_drawing_format": "ANSI Standard Section Drawing"
        },
        "drawing_understanding": {
            "material": matched_drawing["material"],
            "dimensions": matched_drawing["dimensions"],
            "extracted_features": matched_drawing["features"]
        }
    }
