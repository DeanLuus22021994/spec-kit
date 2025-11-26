#!/usr/bin/env python3
"""Result Cache.

Caching layer for validation results to improve performance.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ResultCache:
    """Validation result caching.

    Caches validation results based on file content hash and rule version.
    Invalidates cache when files or rules change.
    """

    def __init__(self, cache_dir: Path, ttl_hours: int = 24) -> None:
        """Initialize cache.

        Args:
            cache_dir: Cache directory.
            ttl_hours: Time-to-live in hours.
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _compute_hash(self, content: str) -> str:
        """Compute content hash.

        Args:
            content: File content.

        Returns:
            SHA256 hash.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_cache_key(self, file_path: Path, rule_version: str, profile: str) -> str:
        """Generate cache key.

        Args:
            file_path: Path to file.
            rule_version: Rule version.
            profile: Validation profile.

        Returns:
            Cache key.
        """
        content = file_path.read_text(encoding="utf-8")
        content_hash = self._compute_hash(content)

        key_parts = [
            str(file_path.relative_to(file_path.parent.parent)),
            content_hash[:16],
            rule_version,
            profile,
        ]

        return "_".join(key_parts).replace("/", "_").replace("\\", "_")

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path.

        Args:
            cache_key: Cache key.

        Returns:
            Cache file path.
        """
        return self.cache_dir / f"{cache_key}.json"

    def get(
        self,
        file_path: Path,
        rule_version: str,
        profile: str,
    ) -> dict[str, Any] | None:
        """Get cached result.

        Args:
            file_path: Path to file.
            rule_version: Rule version.
            profile: Validation profile.

        Returns:
            Cached result or None if not found/expired.
        """
        try:
            cache_key = self._get_cache_key(file_path, rule_version, profile)
            cache_path = self._get_cache_path(cache_key)

            if not cache_path.exists():
                logger.debug("Cache miss: %s", cache_key)
                return None

            # Check TTL
            mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if datetime.now() - mtime > self.ttl:
                logger.debug("Cache expired: %s", cache_key)
                cache_path.unlink()
                return None

            # Load cached result
            with open(cache_path, "r", encoding="utf-8") as f:
                result: dict[str, Any] = json.load(f)

            logger.debug("Cache hit: %s", cache_key)
            return result

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.warning("Cache read error: %s", e)
            return None

    def set(
        self,
        file_path: Path,
        rule_version: str,
        profile: str,
        result: dict[str, Any],
    ) -> None:
        """Cache validation result.

        Args:
            file_path: Path to file.
            rule_version: Rule version.
            profile: Validation profile.
            result: Validation result.
        """
        try:
            cache_key = self._get_cache_key(file_path, rule_version, profile)
            cache_path = self._get_cache_path(cache_key)

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, default=str)

            logger.debug("Cached result: %s", cache_key)

        except (OSError, TypeError) as e:
            logger.warning("Cache write error: %s", e)

    def invalidate(self, file_path: Path | None = None) -> None:
        """Invalidate cache.

        Args:
            file_path: Specific file to invalidate (None = all).
        """
        if file_path:
            # Invalidate specific file
            for cache_file in self.cache_dir.glob("*.json"):
                if str(file_path.name) in cache_file.name:
                    cache_file.unlink()
                    logger.debug("Invalidated cache: %s", cache_file.name)
        else:
            # Invalidate all
            count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1

            logger.info("Invalidated %s cache entries", count)

    def clean_expired(self) -> None:
        """Clean expired cache entries."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime > self.ttl:
                cache_file.unlink()
                count += 1

        logger.info("Cleaned %s expired cache entries", count)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics dictionary.
        """
        cache_files = list(self.cache_dir.glob("*.json"))

        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "entries": len(cache_files),
            "size_bytes": total_size,
            "size_mb": round(total_size / 1024 / 1024, 2),
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl.total_seconds() / 3600,
        }
