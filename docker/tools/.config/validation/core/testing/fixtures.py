#!/usr/bin/env python3
"""
Fixture Generator
Generate test data and fixtures for rule testing.
"""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FixtureGenerator:
    """
    Test fixture generation for validation rules.

    Creates valid and invalid YAML samples for testing.
    """

    def __init__(self, fixtures_dir: Path):
        """
        Initialize fixture generator.

        Args:
            fixtures_dir: Directory for test fixtures
        """
        self.fixtures_dir = fixtures_dir
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)

    def generate_metadata_fixtures(self) -> dict[str, str]:
        """
        Generate metadata validation fixtures.

        Returns:
            Dictionary of fixture name -> content
        """
        return {
            "valid-metadata.yaml": """metadata:
  name: test-file
  version: "1.0.0"
  description: Test file with valid metadata

data:
  key: value
""",
            "invalid-missing-metadata.yaml": """# No metadata block
data:
  key: value
""",
            "invalid-missing-version.yaml": """metadata:
  name: test-file
  description: Missing version field

data:
  key: value
""",
        }

    def generate_indentation_fixtures(self) -> dict[str, str]:
        """
        Generate indentation validation fixtures.

        Returns:
            Dictionary of fixture name -> content
        """
        return {
            "valid-indentation.yaml": """key1:
  nested1:
    deeply:
      value: 1
  nested2:
    value: 2
""",
            "invalid-inconsistent-indentation.yaml": """key1:
  nested1:
      value: 1  # 4 spaces
  nested2:
   value: 2  # 3 spaces
""",
            "invalid-mixed-tabs-spaces.yaml": """key1:
\tnested1:  # tab
  nested2:  # spaces
    value: 1
""",
        }

    def generate_quoting_fixtures(self) -> dict[str, str]:
        """
        Generate quoting validation fixtures.

        Returns:
            Dictionary of fixture name -> content
        """
        return {
            "valid-consistent-quoting.yaml": """strings:
  key1: "double-quoted"
  key2: "also double-quoted"
  key3: "consistent"
""",
            "invalid-mixed-quoting.yaml": """strings:
  key1: "double-quoted"
  key2: 'single-quoted'
  key3: unquoted
""",
        }

    def generate_anchor_fixtures(self) -> dict[str, str]:
        """
        Generate anchor validation fixtures.

        Returns:
            Dictionary of fixture name -> content
        """
        return {
            "valid-anchors.yaml": """defaults: &defaults
  timeout: 30
  retries: 3

service1:
  <<: *defaults
  name: service-1

service2:
  <<: *defaults
  name: service-2
""",
            "invalid-unused-anchor.yaml": """defaults: &defaults
  timeout: 30
  retries: 3

unused: &never_referenced
  key: value

service1:
  name: service-1
""",
            "invalid-undefined-reference.yaml": """service1:
  <<: *undefined_anchor
  name: service-1
""",
        }

    def write_fixtures(self, fixtures: dict[str, str], category: str) -> None:
        """
        Write fixtures to files.

        Args:
            fixtures: Dictionary of filename -> content
            category: Fixture category (e.g., "metadata", "indentation")
        """
        category_dir = self.fixtures_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in fixtures.items():
            fixture_path = category_dir / filename
            fixture_path.write_text(content, encoding="utf-8")
            logger.info("Generated fixture: %s", fixture_path)

    def generate_all_fixtures(self) -> None:
        """Generate all default fixtures."""
        self.write_fixtures(self.generate_metadata_fixtures(), "metadata")
        self.write_fixtures(self.generate_indentation_fixtures(), "indentation")
        self.write_fixtures(self.generate_quoting_fixtures(), "quoting")
        self.write_fixtures(self.generate_anchor_fixtures(), "anchors")

        logger.info("Generated all fixtures")
