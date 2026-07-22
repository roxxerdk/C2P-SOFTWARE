#!/usr/bin/env python
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

# Get all methods
methods = [m for m in dir(client) if not m.startswith("_") and callable(getattr(client, m))]

# Filter for search-related methods
search_methods = [m for m in methods if "search" in m.lower()]

print("Search-related methods:")
for method in sorted(search_methods):
    print(f"  - {method}")
