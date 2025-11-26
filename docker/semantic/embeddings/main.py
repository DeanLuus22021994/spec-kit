"""Embeddings Service - FastAPI Application.

Provides text embedding generation using OpenAI API with Redis caching.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

import uvicorn

try:
    import openai  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional openai dependency
    openai = None  # type: ignore[misc,assignment]
else:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        try:
            openai.api_key = OPENAI_API_KEY
        except AttributeError:
            # newer SDKs may use different client config; we'll set api_key if supported
            pass
import yaml
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

# Handle imports for both standalone and package execution
try:
    from semantic.embeddings.cache import (  # type: ignore[import-not-found]
        EmbeddingCache,
        EmbeddingCacheConfig,
    )
except ImportError:  # pragma: no cover - optional cache
    EmbeddingCache = None  # type: ignore[misc,assignment]
    EmbeddingCacheConfig = None  # type: ignore[misc,assignment]

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="Semantic Kernel Embedding Service",
    description="Text embedding generation service for semantic kernel",
    version="1.0.0",
)


# Models
class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    text: str = Field(..., min_length=1, description="Text to embed")
    model: str = Field(
        default="text-embedding-3-small", description="Embedding model to use"
    )
    user: str | None = Field(None, description="User ID for tracking")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""

    embedding: list[float] = Field(..., description="Vector embedding")
    model: str = Field(..., description="Model used")
    dimensions: int = Field(..., description="Embedding dimensions")
    tokens_used: int = Field(default=0, description="Tokens consumed")
    created_at: str = Field(..., description="Timestamp of creation")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    timestamp: str
    version: str


# Configuration
def load_config() -> dict:
    """Load configuration from YAML file.

    Returns:
        Configuration dictionary.
    """
    config_path = os.getenv("CONFIG_PATH", "/app/config/config.yml")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                result = yaml.safe_load(f)
                return result if isinstance(result, dict) else {}
        else:
            logger.warning("Config file not found at %s, using defaults", config_path)
            return {}
    except (OSError, IOError, yaml.YAMLError) as e:
        logger.error("Error loading config: %s", e)
        return {}


config = load_config()


# Initialize embedding cache
def init_cache() -> Any:
    """Initialize the embedding cache if Redis is available."""
    if EmbeddingCache is None or EmbeddingCacheConfig is None:
        logger.info("Embedding cache not available (cache module not loaded)")
        return None
    try:
        cache_config = EmbeddingCacheConfig.from_env()
        cache = EmbeddingCache(cache_config)
        cache_health = cache.health_check()
        if cache_health["status"] == "healthy":
            logger.info(
                "Embedding cache initialized (Redis at %s:%d)",
                cache_config.host,
                cache_config.port,
            )
            return cache
        logger.warning(
            "Embedding cache unhealthy: %s", cache_health.get("error", "unknown")
        )
        return None
    except Exception as e:  # pylint: disable=broad-except
        logger.warning("Embedding cache initialization failed: %s", e)
        return None


embedding_cache: Any = init_cache()


# OpenAI helpers
def _openai_available() -> bool:
    return openai is not None and bool(os.getenv("OPENAI_API_KEY"))


def generate_embedding_with_openai(text: str, model: str) -> tuple[list[float], int]:
    """Call OpenAI to generate a single embedding; returns (vector, tokens_used).

    If OpenAI is not available, returns a placeholder vector and token estimate.
    """
    dimensions = 1536 if "3-small" in model else 3072
    if not _openai_available():
        return [0.0] * dimensions, len(text.split())
    # Use the OpenAI Embeddings API via getattr to avoid static analysis errors
    embedding_api = getattr(openai, "Embedding", None)
    if embedding_api is None:
        return [0.0] * dimensions, len(text.split())
    resp = embedding_api.create(model=model, input=text)
    vector = resp["data"][0]["embedding"]
    usage = resp.get("usage", {})
    tokens = usage.get("total_tokens", len(text.split()))
    return vector, tokens


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
    resp = embedding_api.create(model=model, input=texts)
    return [d["embedding"] for d in resp["data"]]


# Endpoints
@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint.

    Returns:
        Service information dictionary.
    """
    return {
        "service": "Semantic Kernel Embedding Service",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status response.
    """
    return HealthResponse(
        status="healthy",
        service="embeddings",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


@app.get("/ready", tags=["health"])
async def ready() -> dict:
    """Readiness check endpoint.

    Returns:
        Readiness status dictionary.
    """
    # Check cache connectivity
    cache_health = (
        embedding_cache.health_check() if embedding_cache else {"status": "disabled"}
    )
    return {
        "status": "ready",
        "cache": cache_health.get("status", "unknown"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/embeddings", response_model=EmbeddingResponse, tags=["embeddings"])
async def create_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    """Generate embeddings for the provided text.

    Uses Redis cache for performance - cache hits are ~100x faster than API calls.

    Args:
        request: The embedding request containing text and model.

    Returns:
        Embedding response with vector and metadata.

    Raises:
        HTTPException: If embedding generation fails.
    """
    try:
        # Check cache first
        if embedding_cache:
            cached = embedding_cache.get(request.text, model=request.model)
            if cached:
                logger.info("Cache HIT for embedding (length: %d)", len(request.text))
                return EmbeddingResponse(
                    embedding=cached,
                    model=request.model,
                    dimensions=len(cached),
                    tokens_used=0,  # No tokens used for cache hit
                    created_at=datetime.utcnow().isoformat(),
                )

        logger.info(
            "Cache MISS - Generating embedding for text (length: %d)", len(request.text)
        )

        # Use OpenAI or placeholder implementation
        dimensions = 1536 if "3-small" in request.model else 3072
        tokens_used = len(request.text.split())
        embedding, tokens_used = generate_embedding_with_openai(
            request.text, request.model
        )

        # Cache the result
        if embedding_cache:
            embedding_cache.set(
                request.text,
                embedding,
                model=request.model,
                metadata={"user": request.user} if request.user else None,
            )

        return EmbeddingResponse(
            embedding=embedding,
            model=request.model,
            dimensions=dimensions,
            tokens_used=tokens_used,
            created_at=datetime.utcnow().isoformat(),
        )
    except ValueError as e:
        logger.error("Error generating embedding: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Embedding generation failed: {str(e)}"
        ) from e


@app.post("/embeddings/batch", tags=["embeddings"])
async def create_embeddings_batch(
    texts: list[str], model: str = "text-embedding-3-small"
) -> dict:
    """Generate embeddings for multiple texts in batch.

    Uses Redis cache - only generates embeddings for cache misses.

    Args:
        texts: List of text strings to embed.
        model: The embedding model to use.

    Returns:
        Dictionary containing embeddings and metadata.

    Raises:
        HTTPException: If batch embedding generation fails.
    """
    try:
        logger.info("Generating batch embeddings for %d texts", len(texts))

        cache_hits = 0
        cache_misses = 0
        embeddings: list[list[float] | None] = []

        # Check cache for all texts
        cached_results: dict[str, list[float] | None] = {}
        if embedding_cache:
            cached_results = embedding_cache.get_many(texts, model=model)

        # Process each text
        to_cache: list[tuple[str, list[float]]] = []
        dimensions = 1536 if "3-small" in model else 3072

        miss_texts: list[str] = []
        for text in texts:
            cached = cached_results.get(text)
            if cached:
                embeddings.append(cached)
                cache_hits += 1
            else:
                embeddings.append(None)
                miss_texts.append(text)
                cache_misses += 1

        # Generate embeddings for misses in batch, if any
        generated: list[list[float]] = []
        if miss_texts:
            generated = generate_embeddings_batch_with_openai(miss_texts, model)

        # Fill embeddings and prepare cache list
        to_cache = []
        gen_idx = 0
        for i, text in enumerate(texts):
            if embeddings[i] is None:
                emb = generated[gen_idx]
                embeddings[i] = emb
                to_cache.append((text, emb))
                gen_idx += 1

        # Cache the misses
        if embedding_cache and to_cache:
            embedding_cache.set_many(to_cache, model=model)

        return {
            "embeddings": embeddings,
            "model": model,
            "dimensions": dimensions,
            "count": len(texts),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "created_at": datetime.utcnow().isoformat(),
        }
        # No placeholder implementation remains here
    except ValueError as e:
        logger.error("Error in batch embedding: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Batch embedding failed: {str(e)}"
        ) from e


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> dict[str, Any]:
    """Global exception handler.

    Args:
        _request: The request object (unused).
        exc: The exception that was raised.

    Returns:
        Error response dictionary.
    """
    logger.error("Unhandled exception: %s", exc)
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    reload_enabled = os.getenv("RELOAD", "false").lower() == "true"

    logger.info("Starting Embedding Service on %s:%d", host, port)

    uvicorn.run(
        "main:app", host=host, port=port, reload=reload_enabled, log_level="info"
    )
