"""OpenAI provider for embeddings."""

from __future__ import annotations

import importlib
import os
from typing import Any

# Dynamic import to avoid static analysis errors if package is missing
try:
    openai: Any = importlib.import_module("openai")
except ImportError:
    openai = None


def _openai_available() -> bool:
    """Check if OpenAI is available and configured."""
    return openai is not None and bool(os.getenv("OPENAI_API_KEY"))


def generate_embedding_with_openai(text: str, model: str) -> tuple[list[float], int]:
    """Call OpenAI to generate a single embedding; returns (vector, tokens_used).

    If OpenAI is not available, returns a placeholder vector and token estimate.
    """
    dimensions = 1536 if "3-small" in model else 3072
    if not _openai_available():
        return [0.0] * dimensions, len(text.split())

    # Use the OpenAI Embeddings API via getattr to avoid static analysis errors
    # and handle potential API changes dynamically
    embedding_api = getattr(openai, "Embedding", None)
    if embedding_api is None:
        return [0.0] * dimensions, len(text.split())

    try:
        resp = embedding_api.create(model=model, input=text)
        vector = resp["data"][0]["embedding"]
        usage = resp.get("usage", {})
        tokens = usage.get("total_tokens", len(text.split()))
        return vector, tokens
    except (AttributeError, ValueError, RuntimeError, ImportError):
        # Fallback if API call fails
        return [0.0] * dimensions, len(text.split())


def generate_embeddings_batch_with_openai(
    texts: list[str], model: str
) -> list[list[float]]:
    """Call OpenAI for batch embeddings; fallback to placeholders if unavailable."""
    dimensions = 1536 if "3-small" in model else 3072
    if not _openai_available():
        return [[0.0] * dimensions for _ in texts]

    embedding_api = getattr(openai, "Embedding", None)
    if embedding_api is None:
        return [[0.0] * dimensions for _ in texts]

    try:
        resp = embedding_api.create(model=model, input=texts)
        return [d["embedding"] for d in resp["data"]]
    except (AttributeError, ValueError, RuntimeError, ImportError):
        return [[0.0] * dimensions for _ in texts]
