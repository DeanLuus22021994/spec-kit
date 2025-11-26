#!/usr/bin/env python3
"""
Rule Validator
Validates rule structure against JSON schema.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from types import ModuleType
from typing import Any

JSONSCHEMA: ModuleType | None
try:
    import jsonschema as _jsonschema_module

    JSONSCHEMA = _jsonschema_module
except ImportError:
    JSONSCHEMA = None

logger = logging.getLogger(__name__)


class RuleValidator:
    """
    Rule structure validation using JSON Schema.

    Validates rule definitions against rule-schema.json to ensure
    proper structure and required fields.
    """

    def __init__(self, schema_path: Path | None = None):
        """
        Initialize rule validator.

        Args:
            schema_path: Path to rule-schema.json (optional)
        """
        if not JSONSCHEMA:
            raise ImportError("jsonschema package required for validation")

        self.schema_path = schema_path
        self.schema = self._load_schema() if schema_path else None

    def _load_schema(self) -> dict[str, Any]:
        """
        Load JSON schema.

        Returns:
            Schema dictionary
        """
        if not self.schema_path or not self.schema_path.exists():
            logger.warning("Schema not found: %s", self.schema_path)
            return {}

        with open(self.schema_path, "r", encoding="utf-8") as f:
            schema: dict[str, Any] = json.load(f)
            return schema

    def validate_rule(self, rule: dict[str, Any]) -> dict[str, Any]:
        """
        Validate single rule against schema.

        Args:
            rule: Rule definition

        Returns:
            Validation result with errors if any
        """
        if not self.schema:
            return {
                "valid": False,
                "errors": ["No schema loaded"],
            }

        try:
            JSONSCHEMA.validate(instance=rule, schema=self.schema)  # type: ignore[union-attr]
            return {
                "valid": True,
                "errors": [],
            }
        except JSONSCHEMA.ValidationError as e:  # type: ignore[union-attr]
            return {
                "valid": False,
                "errors": [str(e.message)],
                "path": list(e.path),
            }
        except (TypeError, ValueError) as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {e}"],
            }

    def validate_rules(self, rules: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate multiple rules.

        Args:
            rules: List of rule definitions

        Returns:
            Validation summary
        """
        results = []
        valid_count = 0

        for idx, rule in enumerate(rules):
            result = self.validate_rule(rule)
            result["rule_id"] = rule.get("ruleID", f"rule_{idx}")
            results.append(result)

            if result["valid"]:
                valid_count += 1

        return {
            "total": len(rules),
            "valid": valid_count,
            "invalid": len(rules) - valid_count,
            "results": results,
        }

    def validate_required_fields(self, rule: dict[str, Any]) -> list[str]:
        """
        Check for required fields.

        Args:
            rule: Rule definition

        Returns:
            List of missing fields
        """
        required_fields = [
            "ruleID",
            "description",
            "labels",
            "when",
            "message",
            "effort",
            "category",
        ]

        missing = []
        for field in required_fields:
            if field not in rule:
                missing.append(field)

        return missing

    def validate_field_types(self, rule: dict[str, Any]) -> list[str]:
        """
        Validate field types.

        Args:
            rule: Rule definition

        Returns:
            List of type errors
        """
        errors = []

        # ruleID should be string matching pattern
        if "ruleID" in rule:
            if not isinstance(rule["ruleID"], str):
                errors.append("ruleID must be string")
            elif not rule["ruleID"].strip():
                errors.append("ruleID cannot be empty")

        # labels should be array with at least 2 items
        if "labels" in rule:
            if not isinstance(rule["labels"], list):
                errors.append("labels must be array")
            elif len(rule["labels"]) < 2:
                errors.append("labels must have at least 2 items")

        # effort should be valid value
        if "effort" in rule:
            valid_efforts = [0, 1, 3, 5, 7, 13]
            if rule["effort"] not in valid_efforts:
                errors.append(f"effort must be one of {valid_efforts}")

        # category should be valid
        if "category" in rule:
            valid_categories = ["mandatory", "optional", "potential"]
            if rule["category"] not in valid_categories:
                errors.append(f"category must be one of {valid_categories}")

        return errors

    def validate_rule_structure(self, rule: dict[str, Any]) -> dict[str, Any]:
        """
        Comprehensive rule structure validation.

        Args:
            rule: Rule definition

        Returns:
            Detailed validation result
        """
        errors = []
        warnings = []

        # Required fields
        missing = self.validate_required_fields(rule)
        if missing:
            errors.append(f"Missing required fields: {', '.join(missing)}")

        # Field types
        type_errors = self.validate_field_types(rule)
        errors.extend(type_errors)

        # Warnings for optional best practices
        if "customVariables" not in rule:
            warnings.append("Consider adding customVariables for dynamic content")

        if "links" not in rule:
            warnings.append("Consider adding documentation links")

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "rule_id": rule.get("ruleID", "unknown"),
        }
