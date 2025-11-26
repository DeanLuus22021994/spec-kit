#!/usr/bin/env bash
# Local Build Management Script
# Usage: ./build.sh [command]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly CACHE_DIR="$SCRIPT_DIR/.buildx-cache"

# Ensure cache directories exist
mkdir -p "$CACHE_DIR/redis"
mkdir -p "$CACHE_DIR/database"
mkdir -p "$CACHE_DIR/embeddings"
mkdir -p "$CACHE_DIR/face-matcher"
mkdir -p "$CACHE_DIR/vector"

# Build using Docker Bake
echo "Building local services with optimized caching..."
docker buildx bake --file "$SCRIPT_DIR/docker-bake.hcl" --push

echo "Build complete. Services pushed to local registry."
