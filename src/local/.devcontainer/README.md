# Spec Kit Local Devcontainer

This devcontainer is designed for high-performance local development of the Spec Kit services.

## Features

- **Python 3.13**: Leveraging the latest Python version with support for experimental free-threading (no-GIL) for performance.
- **uv**: Extremely fast Python package installer and resolver.
- **Docker-in-Docker**: Full Docker support to run the service stack via `docker-compose`.
- **Optimized Tooling**: Pre-configured with Ruff (linter/formatter) and Pylance.

## Usage

1. Open the `src/local` folder in VS Code.
2. When prompted, click "Reopen in Container".
3. Once inside, you can use `uv` to manage dependencies and `docker compose` to run the services.

## Services

The `docker-compose.local.yml` defines the following services:
- Database (PostgreSQL + pgvector)
- Redis
- Embeddings Service (GPU enabled)
- Face Matcher Service (GPU enabled)
- Vector Store (Qdrant)
- Jaeger (Tracing)

**Note**: The `embeddings` and `face-matcher` services are configured to use NVIDIA GPUs. Ensure your host machine has the NVIDIA Container Toolkit installed if you plan to run these services with GPU acceleration. If not, you may need to modify the compose file to remove the `deploy.resources` section.

## Network

The devcontainer automatically creates the `spec-kit-infra` network on startup if it doesn't exist.
