import io
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict

import google.generativeai as genai
import pytesseract
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Force load .env from backend root directory
backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=backend_dir / ".env")

MODEL_NAME = "gemini-3.1-flash-lite"


def _catalog_fallback(filename: str) -> Dict[str, Any]:
    """Fallback response when Gemini API is unavailable or unconfigured."""
    return {
        "category": "Plate",
        "material": "Aluminium",
        "dimensions": "100x80x20",
        "confidence": "fallback",
        "needs_review": True,
        "source": "filename_match",
        "features": [
            {
                "id": "feat_1",
                "name": "Through Hole",
                "details": "Dia 10.0mm standard hole",
                "balloon": 1,
            },
            {
                "id": "feat_2",
                "name": "Pocket",
                "details": "Recessed cavity",
                "balloon": 2,
            },
            {
                "id": "feat_3",
                "name": "Chamfer",
                "details": "2mm edge break",
                "balloon": 3,
            },
        ],
        "filename": filename,
    }


def _extract_ocr_numbers(text: Any) -> list:
    if not text:
        return []
    # Force convert to string so re.findall never receives non-string objects
    text_str = str(text) if not isinstance(text, str) else text
    return re.findall(r"\d+(?:\.\d+)?", text_str)


def _compare_dimensions(gemini_dim: Any, ocr_numbers: list) -> bool:
    if not gemini_dim or not ocr_numbers:
        return False
    gemini_nums = _extract_ocr_numbers(gemini_dim)
    return any(num in ocr_numbers for num in gemini_nums)


def _normalize_dimensions(dim_str: Any) -> str:
    if not dim_str:
        return "100x80x20"
    dim_text = str(dim_str)
    nums = _extract_ocr_numbers(dim_text)
    if len(nums) >= 3:
        return f"{nums[0]}x{nums[1]}x{nums[2]}"
    elif len(nums) == 2:
        return f"{nums[0]}x{nums[1]}"
    return dim_text


def analyze_drawing_image(image_bytes: Any, filename: str) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _catalog_fallback(filename)

    genai.configure(api_key=api_key)

    # 1. Robust image loading guard (Handles PIL Image, raw bytes, bytearrays, or open streams)
    if isinstance(image_bytes, Image.Image):
        image = image_bytes
    else:
        try:
            if isinstance(image_bytes, (bytes, bytearray)):
                image = Image.open(io.BytesIO(image_bytes))
            else:
                image = Image.open(image_bytes)
            image.load()
        except Exception as img_err:
            print(f"\n[Image Loading Warning]: {img_err}. Attempting RGB conversion fallback...")
            try:
                if isinstance(image_bytes, (bytes, bytearray)):
                    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                else:
                    image = Image.open(image_bytes).convert("RGB")
            except Exception as final_img_err:
                print(f"\n[Image Loading Exception]: {final_img_err}")
                return _catalog_fallback(filename)

    parsed = None
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = (
            "Extract the drawing metadata as valid JSON with these fields: category, material, dimensions, features. "
            "features must be a list of objects with id, name, details, balloon. "
            "Keep balloon as null for every feature, even though a later agent will assign numbers. "
            "Do not include any markdown, code fences, or explanatory text; return only JSON. "
            "Extract every individually toleranced or inspectable characteristic visible in the drawing body as a separate feature entry. "
            "This includes all holes/bores with diameters and tolerances, all threads, all chamfers and edge breaks, all GD&T frame callouts (flatness, perpendicularity, position, profile, concentricity, etc.) with their tolerance values and datum references, surface finish requirements, break-edge notes, and any dimension line carrying a tolerance. "
            "Do not summarize or group similar features into one entry. "
            "If the drawing shows '2X ⌀.38', that is one feature entry noting quantity 2X, but a separate flatness callout on a different surface is its own feature entry and must not be merged into the hole entry. "
            "If you cannot determine a field, keep it empty or null rather than inventing values."
        )

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = model.generate_content([prompt, image])
                extracted_text = response.text.strip()
                if extracted_text.startswith("```"):
                    extracted_text = re.sub(
                        r"^```(?:json)?\n|\n```$",
                        "",
                        extracted_text,
                        flags=re.MULTILINE,
                    )
                parsed = json.loads(extracted_text)
                break
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg and attempt < max_retries - 1:
                    print(
                        f"\n[Rate Limit 429] Waiting 20 seconds to retry (Attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(20)
                else:
                    raise e

    except Exception as e:
        print(f"\n[Gemini Call Exception]: {e}")
        return _catalog_fallback(filename)

    if not parsed:
        return _catalog_fallback(filename)

    # 2. Safe OCR execution
    ocr_matches = []
    try:
        if isinstance(image, Image.Image):
            ocr_text = pytesseract.image_to_string(image)
            ocr_matches = _extract_ocr_numbers(ocr_text)
    except Exception as ocr_err:
        print(f"\n[OCR Non-Fatal Warning]: {ocr_err}")
        ocr_matches = []

    dimensions = parsed.get("dimensions", "")
    confident = _compare_dimensions(dimensions, ocr_matches)

    return {
        "confidence": "high" if confident else "low",
        "needs_review": not confident,
        "source": "gemini_vision",
        "category": parsed.get("category", "Plate"),
        "material": parsed.get("material", "Aluminium"),
        "dimensions": _normalize_dimensions(dimensions),
        "features": parsed.get("features", []),
        "filename": filename,
    }


# Class wrapper export expected by backend/agents/__init__.py
class perception_agent:
    @staticmethod
    def analyze_drawing_image(image_bytes: Any, filename: str) -> Dict[str, Any]:
        return analyze_drawing_image(image_bytes, filename)


perception_agent_tool = FunctionTool(analyze_drawing_image)
perception_llm_agent = LlmAgent(
    name="perception_agent",
    model=MODEL_NAME,
    description="Analyze engineering drawing images and extract structured metadata and features.",
    instruction=(
        "Use the analyze_drawing_image tool to parse a drawing image and return category, material, dimensions, "
        "and a list of feature objects with id, name, details, and balloon fields."
    ),
    tools=[perception_agent_tool],
)