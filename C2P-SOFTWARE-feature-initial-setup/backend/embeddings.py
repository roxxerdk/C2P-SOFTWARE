import os
from typing import List
import hashlib

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "models/text-embedding-004"
USE_MOCK_EMBEDDINGS = os.environ.get("USE_MOCK_EMBEDDINGS", "false").lower() == "true"


def _mock_embed(text: str) -> List[float]:
    """Generate a deterministic 768-dim mock embedding from text hash."""
    hash_obj = hashlib.sha256(text.encode("utf-8"))
    hash_bytes = hash_obj.digest()
    vector = []
    for i in range(768):
        byte_idx = i % 32
        bit_idx = (i // 32) % 8
        byte_val = hash_bytes[byte_idx]
        bit = (byte_val >> bit_idx) & 1
        vector.append(float(bit) * 2.0 - 1.0)
    return vector


def embed_text(text: str) -> List[float]:
    if USE_MOCK_EMBEDDINGS:
        return _mock_embed(text)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY must be set to embed text.")

    genai.configure(api_key=api_key)
    response = genai.embed_content(model=EMBEDDING_MODEL, content=text)

    if isinstance(response, dict):
        if "embedding" in response:
            return response["embedding"]
        if "data" in response and response["data"]:
            first = response["data"][0]
            if isinstance(first, dict) and "embedding" in first:
                return first["embedding"]
    if hasattr(response, "embedding"):
        return response.embedding
    if hasattr(response, "data") and response.data:
        first = response.data[0]
        if hasattr(first, "embedding"):
            return first.embedding

    raise ValueError("Unable to parse embedding response from Gemini.")
