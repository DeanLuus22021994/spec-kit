"""Embeddings Service - FastAPI Application."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, Request

from .cache import EmbeddingCache, EmbeddingCacheConfig
from .models import EmbeddingRequest, EmbeddingResponse, HealthResponse
from .provider import (
    generate_embedding_with_openai,
    generate_embeddings_batch_with_openai,
)

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


# Configuration
def load_config() -> dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = os.getenv("CONFIG_PATH", "/app/config/config.yml")
    try:
        if os.path.exists(config_path):
            with open(config_path, encoding="utf-8") as f:
                result = yaml.safe_load(f)
                return result if isinstance(result, dict) else {}
        else:
            logger.warning("Config file not found at %s, using defaults", config_path)
            return {}
    except (OSError, yaml.YAMLError) as e:
        logger.error("Error loading config: %s", e)
        return {}


config = load_config()


# Initialize embedding cache
def init_cache() -> EmbeddingCache | None:
    """Initialize the embedding cache if Redis is available."""
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
    except (ValueError, RuntimeError, ImportError):
        logger.warning("Embedding cache initialization failed")
        return None


embedding_cache = init_cache()


# Endpoints
@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "Semantic Kernel Embedding Service",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="embeddings",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
    )


@app.get("/ready", tags=["health"])
async def ready() -> dict[str, str]:
    """Readiness check endpoint."""
    cache_health = (
        embedding_cache.health_check() if embedding_cache else {"status": "disabled"}
    )
    return {
        "status": "ready",
        "cache": str(cache_health.get("status", "unknown")),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/embeddings", response_model=EmbeddingResponse, tags=["embeddings"])
async def create_embedding(request: EmbeddingRequest) -> EmbeddingResponse:
    """Generate embeddings for the provided text."""
    try:
        if embedding_cache:
            cached = embedding_cache.get(request.text, model=request.model)
            if cached:
                logger.info("Cache HIT for embedding (length: %d)", len(request.text))
                return EmbeddingResponse(
                    embedding=cached,
                    model=request.model,
                    dimensions=len(cached),
                    tokens_used=0,
                    created_at=datetime.utcnow().isoformat(),
                )

        logger.info(
            "Cache MISS - Generating embedding for text (length: %d)", len(request.text)
        )

        dimensions = 1536 if "3-small" in request.model else 3072
        embedding, tokens_used = generate_embedding_with_openai(
            request.text, request.model
        )

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
) -> dict[str, Any]:
    """Generate embeddings for multiple texts in batch."""
    try:
        logger.info("Generating batch embeddings for %d texts", len(texts))

        cache_hits = 0
        cache_misses = 0
        embeddings: list[list[float] | None] = []

        cached_results: dict[str, list[float] | None] = {}
        if embedding_cache:
            cached_results = embedding_cache.get_many(texts, model=model)

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

        generated: list[list[float]] = []
        if miss_texts:
            generated = generate_embeddings_batch_with_openai(miss_texts, model)

        to_cache: list[tuple[str, list[float]]] = []
        gen_idx = 0
        for i, text in enumerate(texts):
            if embeddings[i] is None:
                emb = generated[gen_idx]
                embeddings[i] = emb
                to_cache.append((text, emb))
                gen_idx += 1

        if embedding_cache and to_cache:
            embedding_cache.set_many(to_cache, model=model)

        return {
            "embeddings": embeddings,
            "model": model,
            "dimensions": 1536 if "3-small" in model else 3072,
            "count": len(texts),
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "created_at": datetime.utcnow().isoformat(),
        }
    except ValueError as e:
        logger.error("Error in batch embedding: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Batch embedding failed: {str(e)}"
        ) from e


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception) -> dict[str, Any]:
    """Global exception handler."""
    logger.error("Unhandled exception: %s", exc)
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    reload_enabled = os.getenv("RELOAD", "false").lower() == "true"

    logger.info("Starting Embedding Service on %s:%d", host, port)

    uvicorn.run(
        "main:app", host=host, port=port, reload=reload_enabled, log_level="info"
    )
