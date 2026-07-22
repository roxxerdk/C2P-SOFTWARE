#!/usr/bin/env python
import sys
import os

backend_dir = r"c:\Users\pragn.LAPTOP-DAHFBVDA\Downloads\C2P-SOFTWARE-feature-initial-setup\C2P-SOFTWARE-feature-initial-setup\backend"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

try:
    from main import search_knowledge_base, SearchRequest
    
    # Create a search request
    req = SearchRequest(query="deep hole drilling steel", limit=5)
    
    # Call the endpoint handler directly
    result = search_knowledge_base(req)
    
    print(f"✓ Success!")
    print(f"Status: {result.get('status')}")
    print(f"Results count: {len(result.get('results', []))}")
    
    for i, res in enumerate(result.get('results', [])[:2]):
        print(f"\n  Result {i+1}:")
        print(f"    Source: {res.get('source_collection')}")
        print(f"    Score: {res.get('score')}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
