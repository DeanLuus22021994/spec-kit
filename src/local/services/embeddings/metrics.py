"""Cache metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    bytes_saved: int = 0
    compression_ratio: float = 1.0
    avg_latency_ms: float = 0.0
    last_reset: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "hit_rate": f"{self.hit_rate:.2%}",
            "bytes_saved": self.bytes_saved,
            "compression_ratio": f"{self.compression_ratio:.2f}",
            "avg_latency_ms": f"{self.avg_latency_ms:.2f}",
            "last_reset": self.last_reset,
        }
