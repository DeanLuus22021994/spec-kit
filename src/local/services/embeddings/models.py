"""Data models for embedding service."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
