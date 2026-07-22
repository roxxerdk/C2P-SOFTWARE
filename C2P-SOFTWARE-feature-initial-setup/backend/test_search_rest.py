#!/usr/bin/env python
import sys
import os
import json
import hashlib
import numpy as np

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from embeddings import embed_text

# Get a query vector
query = "deep hole drilling steel"
query_vector = embed_text(query)
print(f"Query vector shape: {len(query_vector)}")

# Use requests to call the REST API directly
import requests

QDRANT_URL = "http://localhost:6333"
COLLECTION = "drawings_collection"

# Search endpoint
search_data = {
    "vector": query_vector,
    "limit": 5,
    "with_payload": True,
}

try:
    response = requests.post(
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
        json=search_data,
    )
    print(f"Response status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        print(f"✓ Got {len(result.get('result', []))} results")
        for i, hit in enumerate(result.get('result', [])[:2]):
            print(f"\n  Result {i+1}:")
            print(f"    ID: {hit.get('id')}")
            print(f"    Score: {hit.get('score')}")
            payload = hit.get('payload', {})
            print(f"    Content: {str(payload.get('record'))[:100]}")
    else:
        print(f"✗ Error: {result}")
        
except Exception as e:
    print(f"✗ Exception: {e}")
    import traceback
    traceback.print_exc()
