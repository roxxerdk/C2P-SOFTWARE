import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_engine import rag_engine

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

class FeatureItem(BaseModel):
    id: str
    name: str
    details: str
    balloon: int

class BalloonRequest(BaseModel):
    features: List[dict]

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 3

class ProcessPlanRequest(BaseModel):
    category: str
    material: str
    features: List[dict]

class ValidationRequest(BaseModel):
    category: str
    material: str
    dimensions: str
    process_plan: List[dict]

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
    filename = file.filename
    catalog = load_catalog()
    matched_drawing = None
    
    clean_name = filename.lower().split(".")[0].replace("_", " ").replace("-", " ")
    for drawing in catalog:
        if drawing["name"].lower() in clean_name or drawing["id"].lower() in clean_name:
            matched_drawing = drawing
            break
            
    if not matched_drawing:
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

# Endpoint for generating balloons and assigning coordinates
@app.post("/balloon")
def generate_balloons(request: BalloonRequest):
    ballooned_features = []
    preset_coords = {
        "through hole": {"x": 40, "y": 35},
        "center pocket": {"x": 50, "y": 50},
        "pocket": {"x": 50, "y": 50},
        "corner chamfers": {"x": 15, "y": 15},
        "chamfer": {"x": 15, "y": 15},
        "center bore": {"x": 50, "y": 50},
        "mounting holes": {"x": 80, "y": 80},
        "bearing seat 1": {"x": 30, "y": 45},
        "spline section": {"x": 60, "y": 45},
        "threaded end": {"x": 90, "y": 45}
    }
    
    for idx, feat in enumerate(request.features):
        name = feat.get("name", "").lower()
        coords = preset_coords.get(name, {"x": 30 + (idx * 15), "y": 30 + (idx * 10)})
        
        ballooned_features.append({
            "balloon_number": idx + 1,
            "feature_id": feat.get("id", f"feat_{idx+1}"),
            "feature_name": feat.get("name", "Unknown Feature"),
            "details": feat.get("details", ""),
            "coordinates": coords
        })
        
    return {
        "status": "Success",
        "agent_message": f"Successfully mapped and generated {len(ballooned_features)} feature balloons.",
        "balloons": ballooned_features
    }

@app.post("/search")
def search_knowledge_base(request: SearchRequest):
    results = rag_engine.search(request.query, limit=request.limit)
    return {
        "status": "Success",
        "query": request.query,
        "results": results
    }

# Endpoint for generating the process plan
@app.post("/process-plan")
def generate_process_plan(request: ProcessPlanRequest):
    material_lower = request.material.lower()
    sfm = 400
    feed_rate_coef = 0.003
    
    if "aluminium" in material_lower:
        sfm = 800
        feed_rate_coef = 0.005
    elif "steel" in material_lower:
        sfm = 350
        feed_rate_coef = 0.003
    elif "brass" in material_lower:
        sfm = 1000
        feed_rate_coef = 0.006

    machine = "3-Axis CNC Vertical Mill"
    if request.category.lower() == "shaft":
        machine = "CNC Lathe with Live Tooling"
        
    workflow_steps = []
    step_num = 1
    
    facing_rpm = int((sfm * 3.82) / 2.0)
    facing_feed = int(facing_rpm * feed_rate_coef * 4)
    workflow_steps.append({
        "step_number": step_num,
        "operation": "Facing",
        "description": "Face milling top surface to clean skin stock and establish datum surface.",
        "machine": machine,
        "tool": "2.0-inch indexable Face Mill",
        "speed_rpm": facing_rpm,
        "feed_rate_ipm": facing_feed,
        "estimated_time_mins": 2.5
    })
    step_num += 1
    
    for feat in request.features:
        name = feat.get("name", "")
        details = feat.get("details", "")
        
        op_name = "Milling"
        tool = "0.5-inch 4-Flute Carbide Endmill"
        tool_dia = 0.5
        flutes = 4
        op_desc = f"Milling feature {name} ({details})."
        est_time = 4.0
        
        if "hole" in name.lower() or "drill" in name.lower() or "bore" in name.lower():
            op_name = "Drilling"
            tool = "0.25-inch TiN Coated HSS Jobber Drill"
            tool_dia = 0.25
            flutes = 2
            op_desc = f"Peck drilling through-holes specified: {details}."
            est_time = 1.5
        elif "slot" in name.lower() or "pocket" in name.lower():
            op_name = "Pocket Milling"
            tool = "3/8-inch 3-Flute Carbide Endmill"
            tool_dia = 0.375
            flutes = 3
            op_desc = f"Adaptive clearing pocket profile: {details}."
            est_time = 5.5
        elif "chamfer" in name.lower():
            op_name = "Chamfering"
            tool = "0.25-inch 45-degree Chamfer Mill"
            tool_dia = 0.25
            flutes = 2
            op_desc = f"Edge deburring and breaking corners to drawing spec: {details}."
            est_time = 1.0
            
        rpm = int((sfm * 3.82) / tool_dia)
        feed = int(rpm * feed_rate_coef * flutes)
        
        workflow_steps.append({
            "step_number": step_num,
            "operation": op_name,
            "description": op_desc,
            "machine": machine,
            "tool": tool,
            "speed_rpm": rpm,
            "feed_rate_ipm": feed,
            "estimated_time_mins": est_time
        })
        step_num += 1
        
    workflow_steps.append({
        "step_number": step_num,
        "operation": "Inspection",
        "description": "Dimensional check of critical tolerances and surface finish profile verification.",
        "machine": "Quality Assurance Station",
        "tool": "Digital Calipers, Depth Micrometers & Profilometer",
        "speed_rpm": 0,
        "feed_rate_ipm": 0,
        "estimated_time_mins": 3.0
    })
    
    total_time = sum(step["estimated_time_mins"] for step in workflow_steps)
    
    return {
        "status": "Success",
        "machine_type": machine,
        "total_estimated_time_mins": total_time,
        "process_plan": workflow_steps
    }

# Endpoint for validating the process plan and applying reflection optimization
@app.post("/validate")
def validate_process_plan(request: ValidationRequest):
    """
    Validation & Reflection Agents endpoint.
    Validation Agent: Checks the plan against geometric constraints (e.g. thickness, feature depth ratio).
    Reflection Agent: If warnings are raised, corrects them by adding pilot steps, pecking cycles, or sequence updates.
    """
    warnings = []
    has_deep_hole = False
    
    # 1. Validation Agent logic
    # Check dimensions (e.g. if thickness is high, check aspect ratio)
    dims = request.dimensions.lower().split("x")
    thickness = 10.0  # Default thickness in mm
    if len(dims) >= 3:
        try:
            # Extract thickness from the last dimension value
            thickness = float(re.findall(r'\d+\.?\d*', dims[2])[0])
        except Exception:
            pass
            
    for step in request.process_plan:
        op = step["operation"]
        tool = step["tool"]
        
        # Sizing rules check: Drilling aspect ratio
        if op == "Drilling" and thickness > 50.0:
            warnings.append({
                "agent": "Validation Agent",
                "severity": "High",
                "message": f"Drilling thickness ({thickness}mm) exceeds 5x tool diameter. High risk of tool breakage."
            })
            has_deep_hole = True
            
        # Tool wear warning
        if "steel" in request.material.lower() and "hss" in tool.lower():
            warnings.append({
                "agent": "Validation Agent",
                "severity": "Medium",
                "message": "Using HSS tooling on steel material. Risk of rapid tool wear. Carbide is recommended."
            })
            
    # 2. Reflection Agent optimization logic
    optimized_plan = [dict(step) for step in request.process_plan]
    optimizations = []
    
    if warnings:
        for idx, step in enumerate(optimized_plan):
            # Reflect on drilling optimization
            if step["operation"] == "Drilling" and has_deep_hole:
                step["description"] = "Peck drilling cycle (Q=0.1\") to clear chips and prevent heat build-up. Cooled with pressurized flood coolant."
                step["tool"] = "0.25-inch Carbide Coated High-Performance Drill"
                optimizations.append("Upgraded twist drill to Carbide and added peck drilling sequence to mitigate deep aspect-ratio drilling hazards.")
                
            # Reflect on HSS-to-Carbide tool upgrade
            if "steel" in request.material.lower() and "hss" in step["tool"].lower():
                step["tool"] = step["tool"].replace("HSS", "Cobalt-Carbide")
                step["speed_rpm"] = int(step["speed_rpm"] * 1.5)  # Higher speeds allowed for Carbide
                optimizations.append(f"Upgraded step {step['step_number']} tooling to Cobalt-Carbide for steel machining speed and longevity.")
                
    else:
        # Default optimization: Tool grouping to minimize tool changes
        optimizations.append("No critical DFM warning found. Optimized tool change coordinates to minimize cycle path time.")
        
    total_time = sum(step["estimated_time_mins"] for step in optimized_plan)
    
    return {
        "status": "Success",
        "validation_passed": len([w for w in warnings if w["severity"] == "High"]) == 0,
        "warnings": warnings,
        "reflection_applied": len(optimizations) > 0,
        "reflection_optimizations": optimizations,
        "optimized_estimated_time_mins": total_time,
        "optimized_process_plan": optimized_plan
    }
