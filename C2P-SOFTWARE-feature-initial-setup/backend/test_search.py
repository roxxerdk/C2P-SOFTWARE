#!/usr/bin/env python
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

try:
    from rag_engine import semantic_search
    print("Testing semantic_search function...")
    results = semantic_search("deep hole drilling steel", top_k=5)
    print(f"✓ Got {len(results)} results")
    for i, result in enumerate(results):
        print(f"\n  Result {i+1}:")
        print(f"    Source: {result.get('source_collection')}")
        print(f"    Score: {result.get('score')}")
        print(f"    Content type: {type(result.get('content'))}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
