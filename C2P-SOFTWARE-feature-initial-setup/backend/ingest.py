import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from embeddings import embed_text
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

from qdrant_config import (
    DRAWINGS_COLLECTION,
    MATERIALS_COLLECTION,
    PROCESS_TEMPLATES_COLLECTION,
    TOOLS_COLLECTION,
    STANDARDS_COLLECTION,
    ensure_collections,
    get_qdrant_client,
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATASET_DIR = PROJECT_ROOT / "dataset"


def _deterministic_point_id(source: str, record_id: str) -> int:
    digest = hashlib.sha256(f"{source}|{record_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big") & 0x7FFFFFFFFFFFFFFF


def _read_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_text_file(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def _chunk_text(text: str, max_words: int = 300) -> List[str]:
    words = text.split()
    return [" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words)]


def _upsert_points(collection_name: str, points: List[PointStruct]) -> int:
    client: QdrantClient = get_qdrant_client()
    if not points:
        return 0
    client.upsert(collection_name=collection_name, points=points)
    return len(points)


def ingest_drawings() -> int:
    source_file = "dataset/drawings/drawings_catalog.json"
    data = _read_json_file(DATASET_DIR / "drawings" / "drawings_catalog.json")
    points: List[PointStruct] = []

    for record in data:
        record_id = str(record.get("id", record.get("name", "")))
        embedding_text = (
            f"{record.get('name', '')} ({record.get('category', '')}) in {record.get('material', '')}, "
            f"dimensions {record.get('dimensions', '')}. Features: "
            + ", ".join(
                [f"{feat.get('name', '')} {feat.get('details', '')}" for feat in record.get("features", [])]
            )
        )
        vector = embed_text(embedding_text)
        payload = {
            "source_file": source_file,
            "record_type": "drawing",
            "record": record,
        }
        point_id = _deterministic_point_id(source_file, record_id)
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    return _upsert_points(DRAWINGS_COLLECTION, points)


def ingest_materials() -> int:
    materials_dir = DATASET_DIR / "materials"
    points: List[PointStruct] = []

    for file_path in sorted(materials_dir.glob("*.json")):
        record = _read_json_file(file_path)
        material_name = record.get("material_name", "")
        default_grade = record.get("default_grade", "")
        properties = record.get("properties", {})
        machining = record.get("machining_parameters", {})

        properties_text = ", ".join(
            [f"{k.replace('_', ' ')} {v}" for k, v in properties.items() if v]
        )
        machining_text = ", ".join(
            [f"{k.replace('_', ' ')} {v}" for k, v in machining.items() if v]
        )

        embedding_text = (
            f"{material_name} ({default_grade}): {properties_text}. "
            f"Machining parameters include {machining_text}."
        )

        vector = embed_text(embedding_text)
        payload = {
            "source_file": f"dataset/materials/{file_path.name}",
            "record_type": "material",
            "record": record,
        }
        point_id = _deterministic_point_id(str(file_path), material_name)
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    return _upsert_points(MATERIALS_COLLECTION, points)


def ingest_process_templates() -> int:
    templates_dir = DATASET_DIR / "process_templates"
    points: List[PointStruct] = []

    for file_path in sorted(templates_dir.glob("*.json")):
        record = _read_json_file(file_path)
        process_type = record.get("process_type", "")
        steps = record.get("steps", [])
        steps_text = "; ".join(
            [f"{step.get('name', '')}: {step.get('purpose', '')}" for step in steps]
        )
        embedding_text = (
            f"Process template for {process_type}. Steps include {steps_text}."
        )

        vector = embed_text(embedding_text)
        payload = {
            "source_file": f"dataset/process_templates/{file_path.name}",
            "record_type": "process_template",
            "record": record,
        }
        point_id = _deterministic_point_id(str(file_path), process_type)
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    return _upsert_points(PROCESS_TEMPLATES_COLLECTION, points)


def ingest_tools() -> int:
    tools_dir = DATASET_DIR / "tools"
    points: List[PointStruct] = []

    for file_path in sorted(tools_dir.glob("*.json")):
        record = _read_json_file(file_path)
        tool_type = record.get("tool_type", "")
        configurations = record.get("configurations", [])
        config_text = "; ".join(
            [
                f"{conf.get('diameter_inch', '')}-inch {conf.get('material', '')} with {conf.get('coating', '')} coating for {', '.join(conf.get('recommended_operations', []))}"
                for conf in configurations
            ]
        )
        embedding_text = (
            f"Tool type {tool_type}. Configurations include {config_text}."
        )

        vector = embed_text(embedding_text)
        payload = {
            "source_file": f"dataset/tools/{file_path.name}",
            "record_type": "tool",
            "record": record,
        }
        point_id = _deterministic_point_id(str(file_path), tool_type)
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    return _upsert_points(TOOLS_COLLECTION, points)


def ingest_standards() -> int:
    standards_dir = DATASET_DIR / "standards"
    points: List[PointStruct] = []

    for file_path in sorted(standards_dir.glob("*.md")):
        raw_text = _read_text_file(file_path)
        chunks = _chunk_text(raw_text, max_words=300)

        for index, chunk in enumerate(chunks):
            embedding_text = f"Standard document chunk from {file_path.name}: {chunk[:600]}"
            vector = embed_text(embedding_text)
            payload = {
                "source_file": f"dataset/standards/{file_path.name}",
                "record_type": "standard_chunk",
                "chunk_index": index,
                "chunk_text": chunk,
            }
            point_id = _deterministic_point_id(f"dataset/standards/{file_path.name}", str(index))
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    return _upsert_points(STANDARDS_COLLECTION, points)


def main():
    ensure_collections()

    summary = {
        DRAWINGS_COLLECTION: ingest_drawings(),
        MATERIALS_COLLECTION: ingest_materials(),
        PROCESS_TEMPLATES_COLLECTION: ingest_process_templates(),
        TOOLS_COLLECTION: ingest_tools(),
        STANDARDS_COLLECTION: ingest_standards(),
    }

    print("Ingestion summary:")
    for collection, count in summary.items():
        print(f"- {collection}: {count} points upserted")


if __name__ == "__main__":
    main()
