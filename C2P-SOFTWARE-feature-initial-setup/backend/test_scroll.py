#!/usr/bin/env python
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

try:
    from qdrant_config import get_qdrant_client, DRAWINGS_COLLECTION, MATERIALS_COLLECTION
    client = get_qdrant_client()
    
    print("Testing scroll method...")
    points, next_page = client.scroll(
        collection_name=DRAWINGS_COLLECTION,
        limit=5,
        with_payload=True,
    )
    print(f"✓ Retrieved {len(points)} points from {DRAWINGS_COLLECTION}")
    
    for i, point in enumerate(points[:2]):
        print(f"\n  Point {i+1}:")
        print(f"    ID: {point.id}")
        print(f"    Has vector: {hasattr(point, 'vector') and point.vector is not None}")
        print(f"    Payload keys: {list(point.payload.keys()) if hasattr(point, 'payload') else 'N/A'}")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
