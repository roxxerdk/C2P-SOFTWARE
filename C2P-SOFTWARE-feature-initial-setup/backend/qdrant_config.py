import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

load_dotenv()

QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

DRAWINGS_COLLECTION = "drawings_collection"
MATERIALS_COLLECTION = "materials_collection"
PROCESS_TEMPLATES_COLLECTION = "process_templates_collection"
TOOLS_COLLECTION = "tools_collection"
STANDARDS_COLLECTION = "standards_collection"

_qdrant_client = None


def get_qdrant_client():
    global _qdrant_client
    if _qdrant_client is None:
        client_kwargs = {"url": QDRANT_URL}
        if QDRANT_API_KEY:
            client_kwargs["api_key"] = QDRANT_API_KEY
        _qdrant_client = QdrantClient(**client_kwargs)
    return _qdrant_client


def _collection_exists(client: QdrantClient, collection_name: str) -> bool:
    try:
        client.get_collection(collection_name=collection_name)
        return True
    except Exception:
        return False


def ensure_collections():
    client = get_qdrant_client()
    collections = [
        DRAWINGS_COLLECTION,
        MATERIALS_COLLECTION,
        PROCESS_TEMPLATES_COLLECTION,
        TOOLS_COLLECTION,
        STANDARDS_COLLECTION,
    ]

    for collection_name in collections:
        if not _collection_exists(client, collection_name):
            client.create_collection(
                collection_name=collection_name,
                vectors_config=rest.VectorParams(size=768, distance=rest.Distance.COSINE),
            )
