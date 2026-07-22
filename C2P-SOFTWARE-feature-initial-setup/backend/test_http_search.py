#!/usr/bin/env python
import json
import requests

try:
    response = requests.post(
        "http://localhost:8000/search",
        json={"query": "deep hole drilling steel", "limit": 5},
        timeout=10,
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Got {len(data)} results\n")
        for i, result in enumerate(data[:3]):
            print(f"Result {i+1}:")
            print(f"  Source: {result.get('source_collection')}")
            print(f"  Score: {result.get('score')}")
            content = result.get('content', {})
            if isinstance(content, dict):
                print(f"  Type: {content.get('category', 'Unknown')}")
            print()
    else:
        print(f"✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Exception: {e}")
