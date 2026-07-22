import json
import os
import requests
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from qdrant_config import (
    get_qdrant_client,
    DRAWINGS_COLLECTION,
    MATERIALS_COLLECTION,
    PROCESS_TEMPLATES_COLLECTION,
    TOOLS_COLLECTION,
    STANDARDS_COLLECTION,
)
from qdrant_client.http import models as rest
from embeddings import embed_text

DATASET_DIR = Path(__file__).resolve().parent.parent / "dataset"
ALL_COLLECTIONS = [
    DRAWINGS_COLLECTION,
    MATERIALS_COLLECTION,
    PROCESS_TEMPLATES_COLLECTION,
    TOOLS_COLLECTION,
    STANDARDS_COLLECTION,
]


def _legacy_keyword_search(query: str, limit: int = 3):
    dataset_dir = DATASET_DIR
    knowledge_base = []

    # 1. Load Standards (Markdown)
    standards_dir = dataset_dir / "standards"
    if standards_dir.exists():
        for file_path in sorted(standards_dir.glob("*.md")):
            content = file_path.read_text(encoding="utf-8")
            knowledge_base.append({
                "source": f"standards/{file_path.name}",
                "title": file_path.stem.replace("_", " ").title(),
                "content": content,
                "type": "standard",
            })

    # 2. Load Process Templates (JSON)
    templates_dir = dataset_dir / "process_templates"
    if templates_dir.exists():
        for file_path in sorted(templates_dir.glob("*.json")):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            knowledge_base.append({
                "source": f"process_templates/{file_path.name}",
                "title": f"{data.get('process_type')} Template",
                "content": json.dumps(data, indent=2),
                "type": "template",
            })

    # 3. Load Tools (JSON)
    tools_dir = dataset_dir / "tools"
    if tools_dir.exists():
        for file_path in sorted(tools_dir.glob("*.json")):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            knowledge_base.append({
                "source": f"tools/{file_path.name}",
                "title": f"{data.get('tool_type')} Documentation",
                "content": json.dumps(data, indent=2),
                "type": "tool",
            })

    # 4. Load Materials (JSON)
    materials_dir = dataset_dir / "materials"
    if materials_dir.exists():
        for file_path in sorted(materials_dir.glob("*.json")):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            knowledge_base.append({
                "source": f"materials/{file_path.name}",
                "title": f"{data.get('material_name')} Material Properties",
                "content": json.dumps(data, indent=2),
                "type": "material",
            })

    results = []
    query_words = [word for word in query.lower().split() if word]

    for item in knowledge_base:
        score = 0
        content_lower = item["content"].lower()
        title_lower = item["title"].lower()

        for word in query_words:
            if word in title_lower:
                score += 10
            score += content_lower.count(word)

        if score > 0:
            results.append({
                "score": score,
                "title": item["title"],
                "source": item["source"],
                "type": item["type"],
                "content": item["content"],
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def _format_qdrant_hit(collection_name: str, hit: Dict[str, Any]) -> Dict[str, Any]:
    # Handle REST API response format
    payload = hit.get("payload", {})
    score = hit.get("score", 0)
    content = payload.get("chunk_text") if payload.get("chunk_text") else payload.get("record")
    return {
        "content": content,
        "source_collection": collection_name,
        "score": score,
        "payload": payload,
    }


def _qdrant_search_collection(collection_name: str, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
    # Get QDRANT_URL from environment
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    try:
        # Use REST API for compatibility with version mismatch
        search_data = {
            "vector": query_vector,
            "limit": top_k,
            "with_payload": True,
        }
        
        response = requests.post(
            f"{qdrant_url}/collections/{collection_name}/points/search",
            json=search_data,
            timeout=10,
        )
        
        if response.status_code == 200:
            result = response.json()
            hits = result.get("result", [])
            return [_format_qdrant_hit(collection_name, hit) for hit in hits]
        else:
            print(f"Qdrant search error: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"Error searching {collection_name}: {e}")
        return []


def semantic_search(query: str, collections: Optional[List[str]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    target_collections = collections if collections is not None else ALL_COLLECTIONS
    query_vector = embed_text(query)
    merged_results: List[Dict[str, Any]] = []

    for collection_name in target_collections:
        merged_results.extend(_qdrant_search_collection(collection_name, query_vector, top_k))

    merged_results.sort(key=lambda item: item.get("score", 0), reverse=True)
    return merged_results[:top_k]


def write_plan_to_memory(drawing_data: Dict[str, Any], plan: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Embed and upsert a generated validated process plan into the process_templates collection."""
    title = f"Generated plan for {drawing_data.get('category', 'Unknown')} - {drawing_data.get('material', 'Unknown')}"
    record_text = json.dumps({
        "drawing_data": drawing_data,
        "process_plan": plan,
        "warnings": warnings,
    }, indent=2)
    embedding = embed_text(title + "\n" + record_text)

    client = get_qdrant_client()
    collection_name = PROCESS_TEMPLATES_COLLECTION

    payload = {
        "source": "generated",
        "drawing_category": drawing_data.get("category", "Unknown"),
        "material": drawing_data.get("material", "Unknown"),
        "dimensions": drawing_data.get("dimensions", ""),
        "plan_summary": title,
        "warnings": warnings,
    }

    point = {
        "id": str(uuid.uuid4()),
        "vector": embedding,
        "payload": payload,
    }

    try:
        client.upsert(collection_name=collection_name, points=[point])
        return {"status": "success", "point_id": point["id"], "collection": collection_name}
    except Exception as e:
        print(f"Error writing plan to Qdrant: {e}")
        raise


class LocalRAGEngine:
    def search(self, query: str, limit: int = 3):
        return semantic_search(query, top_k=limit)


rag_engine = LocalRAGEngine()
