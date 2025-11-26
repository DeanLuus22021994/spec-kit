#!/usr/bin/env python3
"""Test OpenAI integration."""

from __future__ import annotations

from services.embeddings.provider import (
    generate_embedding_with_openai,
    generate_embeddings_batch_with_openai,
)


def main() -> None:
    """Run OpenAI tests."""
    print(
        "single len",
        len(generate_embedding_with_openai("test", "text-embedding-3-small")[0]),
    )
    print(
        "batch len",
        len(
            generate_embeddings_batch_with_openai(["a", "b"], "text-embedding-3-small")[
                0
            ]
        ),
    )


if __name__ == "__main__":
    main()
