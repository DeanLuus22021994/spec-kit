#!/usr/bin/env python3
"""Documentation Generator for Semantic Kernel App.

Automatically generates documentation from code comments and API schemas.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class DocGenerator:
    """Generates documentation from source code and configuration files."""

    def __init__(self, config_path: str = ".config/cli.yml") -> None:
        """Initialize the documentation generator.

        Args:
            config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.output_dir = Path("docs/api")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary.
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if config is not None else {}
        except FileNotFoundError:
            msg = f"Warning: Config file {self.config_path} " "not found. Using defaults."
            print(msg)
            return {}

    def generate_api_docs(self) -> None:
        """Generate API documentation from OpenAPI specs."""
        print("Generating API documentation...")

        # Backend API
        backend_doc = self._generate_service_doc(
            "Backend API",
            "Main application backend service",
            [
                ("GET", "/health", "Health check endpoint"),
                ("GET", "/api/semantic/status", "Get service status"),
                ("POST", "/api/semantic/query", "Submit semantic query"),
            ],
        )
        self._write_doc("backend-api.md", backend_doc)

        # Engine API
        engine_doc = self._generate_service_doc(
            "Semantic Kernel Engine",
            "AI processing and semantic kernel operations",
            [
                ("POST", "/api/kernel/chat", "Chat completion"),
                ("POST", "/api/kernel/embedding", "Generate embeddings"),
                ("POST", "/api/kernel/completion", "Text completion"),
            ],
        )
        self._write_doc("engine-api.md", engine_doc)

        # Vector Store API
        vector_doc = self._generate_service_doc(
            "Vector Store API",
            "Qdrant vector database operations",
            [
                ("GET", "/collections", "List collections"),
                (
                    "POST",
                    "/collections/{name}/points",
                    "Upsert vectors",
                ),
                (
                    "POST",
                    "/collections/{name}/points/search",
                    "Search vectors",
                ),
            ],
        )
        self._write_doc("vector-api.md", vector_doc)

        # Embeddings API
        embeddings_doc = self._generate_service_doc(
            "Embeddings Service",
            "Text embedding generation service",
            [
                ("POST", "/api/embeddings", "Generate single embedding"),
                ("POST", "/api/embeddings/batch", "Generate batch embeddings"),
                ("GET", "/health", "Health check"),
            ],
        )
        self._write_doc("embeddings-api.md", embeddings_doc)

        print(f"API documentation generated in {self.output_dir}")

    def _generate_service_doc(
        self,
        title: str,
        description: str,
        endpoints: list[tuple[str, str, str]],
    ) -> str:
        """Generate markdown documentation for a service.

        Args:
            title: The service title.
            description: The service description.
            endpoints: List of (method, path, description) tuples.

        Returns:
            Markdown documentation string.
        """
        doc = f"""# {title}

{description}

**Base URL:** `http://localhost:8080/api`

## Endpoints

"""
        for method, path, desc in endpoints:
            doc += f"### `{method} {path}`\n\n{desc}\n\n"
            doc += "**Request:**\n```json\n{\n  // Request body\n}\n```\n\n"
            doc += "**Response:**\n```json\n{\n  // Response body\n}\n```\n\n"
            doc += "---\n\n"

        doc += f"\n_Generated: {datetime.now().isoformat()}_\n"
        return doc

    def _write_doc(self, filename: str, content: str) -> None:
        """Write documentation to file.

        Args:
            filename: The output filename.
            content: The documentation content.
        """
        filepath = self.output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ {filepath}")

    def generate_architecture_doc(self) -> None:
        """Generate architecture documentation."""
        print("Generating architecture documentation...")

        arch_doc = """# System Architecture

## Overview

The Semantic Kernel App is a microservices-based application for
AI-powered semantic search and processing.

## Services

### Frontend (React + Semantic UI)
- **Port:** 3000
- **Technology:** React 18, TypeScript, Semantic UI React
- **Purpose:** User interface for semantic queries

### Backend (ASP.NET Core)
- **Port:** 5000
- **Technology:** .NET 6, Kestrel
- **Purpose:** Main API gateway and business logic

### Engine (Semantic Kernel)
- **Port:** Internal
- **Technology:** .NET 6, Microsoft.SemanticKernel
- **Purpose:** AI processing, kernel operations

### Gateway (API Gateway)
- **Port:** 8080
- **Technology:** .NET 6, Kestrel
- **Purpose:** Reverse proxy and routing

### Vector Store (Qdrant)
- **Port:** 6333 (HTTP), 6334 (gRPC)
- **Technology:** Qdrant v1.7.4
- **Purpose:** Vector similarity search

### Embeddings Service (FastAPI)
- **Port:** 8001
- **Technology:** Python 3.11, FastAPI
- **Purpose:** Generate text embeddings

### Database (PostgreSQL)
- **Port:** 5432
- **Technology:** PostgreSQL 16
- **Purpose:** Persistent data storage

### Nginx (Reverse Proxy)
- **Port:** 80
- **Technology:** Nginx Alpine
- **Purpose:** Load balancing and routing

## Communication Flow

```
User → Nginx → Gateway → Backend → Engine → Embeddings/Vector
                                  ↓
                              Database
```

## Deployment

All services are containerized with Docker and orchestrated using
Docker Compose.

**Network:** 172.20.0.0/16 (production), 172.21.0.0/16 (development)

"""
        self._write_doc("architecture.md", arch_doc)

    def generate_all(self) -> None:
        """Generate all documentation."""
        self.generate_api_docs()
        self.generate_architecture_doc()
        print("\n✓ Documentation generation complete!")


def main() -> None:
    """Command-line entry point for docgen.

    Parses arguments and runs the appropriate generation commands.
    """
    parser = argparse.ArgumentParser(description="Generate documentation for Semantic Kernel App")
    parser.add_argument(
        "--config",
        default=".config/cli.yml",
        help="Path to config file",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Generate API docs only",
    )
    parser.add_argument(
        "--arch",
        action="store_true",
        help="Generate architecture docs only",
    )

    args = parser.parse_args()

    generator = DocGenerator(config_path=args.config)

    if args.api:
        generator.generate_api_docs()
    elif args.arch:
        generator.generate_architecture_doc()
    else:
        generator.generate_all()


if __name__ == "__main__":
    main()
