#!/usr/bin/env python
import os
import sys
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Set paths and ensure backend folder is in sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

# Force environment loading before importing perception_agent
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

from agents.perception_agent import analyze_drawing_image


def get_sample_image(project_root: Path) -> Path:
    sample_path = project_root / "dataset" / "drawings" / "test_image.png"
    if sample_path.exists():
        return sample_path
    raise FileNotFoundError(
        "No sample image found at dataset/drawings/test_image.png. "
        "Please add your drawing image there."
    )


def print_result(case_name: str, result: dict) -> None:
    print(f"\n=== {case_name} ===")
    print(f"category: {result.get('category')}")
    print(f"material: {result.get('material')}")
    print(f"dimensions: {result.get('dimensions')}")
    print(f"confidence: {result.get('confidence')}")
    print(f"needs_review: {result.get('needs_review')}")
    print(f"source: {result.get('source')}")
    print(f"features: {result.get('features')}")


def main():
    project_root = backend_dir.parent
    image_path = get_sample_image(project_root)
    image_bytes = image_path.read_bytes()

    original_key = os.environ.get("GEMINI_API_KEY")
    test_results = []

    # Case 1: Fallback path test by clearing API key from environment
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    try:
        fallback_result = analyze_drawing_image(image_bytes, "dr_plate_01.png")
        print_result("Fallback path (GEMINI_API_KEY unset)", fallback_result)
        fallback_pass = (
            fallback_result.get("confidence") == "fallback"
            and fallback_result.get("source") == "filename_match"
        )
        test_results.append(("fallback", fallback_pass, fallback_result))
    except Exception:
        print("\nFallback path threw an exception:")
        traceback.print_exc()
        test_results.append(("fallback", False, {}))

    # Restore original key for Gemini API test
    if original_key:
        os.environ["GEMINI_API_KEY"] = original_key

    # Case 2: Live Gemini API Vision test
    if os.environ.get("GEMINI_API_KEY"):
        try:
            real_result = analyze_drawing_image(image_bytes, image_path.name)
            print_result("Gemini + OCR path", real_result)
            real_pass = (
                isinstance(real_result, dict)
                and real_result.get("confidence") != "fallback"
            )
            test_results.append(("gemini", real_pass, real_result))
        except Exception:
            print("\nGemini path threw an exception:")
            traceback.print_exc()
            test_results.append(("gemini", False, {}))
    else:
        print("\nSkipping Gemini path: GEMINI_API_KEY not set.")
        test_results.append(("gemini", True, {"skipped": True}))

    passed = sum(1 for _, ok, _ in test_results if ok)
    total = len(test_results)
    print(f"\n=== Summary: {passed}/{total} tests passed ===")
    for name, ok, result in test_results:
        status = "PASS" if ok else "FAIL"
        print(f"- {name}: {status}")
    if passed == total:
        print("All perception tests passed.")
        sys.exit(0)
    print("Some perception tests failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()