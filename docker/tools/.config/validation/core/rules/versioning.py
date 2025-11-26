#!/usr/bin/env python3
"""
Rule Versioning
Track rule changes and versions for audit trail.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

_yaml: ModuleType | None
try:
    import yaml as _yaml_module

    _yaml = _yaml_module
except ImportError:
    _yaml = None

logger = logging.getLogger(__name__)


class RuleVersioning:
    """
    Rule change tracking and versioning.

    Maintains history of rule changes for audit and rollback.
    Uses content hashing to detect changes.
    """

    def __init__(self, versions_file: Path):
        """
        Initialize versioning tracker.

        Args:
            versions_file: Path to versions.yaml
        """
        if not _yaml:
            raise ImportError("PyYAML required for versioning")

        self.versions_file = versions_file
        self.versions: dict[str, list[dict[str, Any]]] = {}

        # Load existing versions
        if self.versions_file.exists():
            self._load_versions()

    def _load_versions(self) -> None:
        """Load version history from file."""
        with open(self.versions_file, "r", encoding="utf-8") as f:
            data = _yaml.safe_load(f) if _yaml else None

        self.versions = data or {}
        logger.info("Loaded %d rule version histories", len(self.versions))

    def _save_versions(self) -> None:
        """Save version history to file."""
        self.versions_file.parent.mkdir(parents=True, exist_ok=True)

        if _yaml:
            with open(self.versions_file, "w", encoding="utf-8") as f:
                _yaml.dump(self.versions, f, default_flow_style=False, sort_keys=False)

        logger.debug("Saved version history")

    def _compute_hash(self, rule: dict[str, Any]) -> str:
        """
        Compute content hash for rule.

        Args:
            rule: Rule definition

        Returns:
            SHA256 hash
        """
        # Create canonical representation
        canonical = json.dumps(rule, sort_keys=True)

        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def record_rule(self, rule: dict[str, Any], change_type: str = "update") -> None:
        """
        Record rule version.

        Args:
            rule: Rule definition
            change_type: Type of change (create, update, delete)
        """
        rule_id = rule.get("ruleID")
        if not rule_id:
            logger.warning("Cannot version rule without ruleID")
            return

        # Compute hash
        content_hash = self._compute_hash(rule)

        # Get existing history
        history = self.versions.get(rule_id, [])

        # Check if this version already recorded
        if history and history[-1].get("hash") == content_hash:
            logger.debug("Rule %s unchanged, skipping version", rule_id)
            return

        # Create version record
        version_record = {
            "timestamp": datetime.now().isoformat(),
            "hash": content_hash,
            "change_type": change_type,
            "version": len(history) + 1,
            "package": rule.get("_package", "unknown"),
            "category": rule.get("category"),
        }

        history.append(version_record)
        self.versions[rule_id] = history

        logger.info("Recorded version %d for rule %s", version_record["version"], rule_id)

        # Save to disk
        self._save_versions()

    def get_rule_history(self, rule_id: str) -> list[dict[str, Any]]:
        """
        Get version history for rule.

        Args:
            rule_id: Rule identifier

        Returns:
            List of version records
        """
        return self.versions.get(rule_id, [])

    def get_latest_version(self, rule_id: str) -> dict[str, Any] | None:
        """
        Get latest version record.

        Args:
            rule_id: Rule identifier

        Returns:
            Latest version record or None
        """
        history = self.get_rule_history(rule_id)
        return history[-1] if history else None

    def detect_changes(self, current_rules: list[dict[str, Any]]) -> dict[str, list[str]]:
        """
        Detect changes in current rules vs. versioned.

        Args:
            current_rules: Current rule definitions

        Returns:
            Dictionary of changed rules by type
        """
        changes: dict[str, list[str]] = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": [],
        }

        current_ids = {rule.get("ruleID") for rule in current_rules}
        versioned_ids = set(self.versions.keys())

        # Detect new rules
        new_ids = current_ids - versioned_ids
        changes["created"] = [str(rule_id) for rule_id in new_ids if rule_id is not None]

        # Detect deleted rules
        deleted_ids = versioned_ids - current_ids
        changes["deleted"] = [str(rule_id) for rule_id in deleted_ids if rule_id is not None]

        # Detect updated rules
        for rule in current_rules:
            rule_id = rule.get("ruleID")
            if rule_id in versioned_ids:
                current_hash = self._compute_hash(rule)
                latest_version = self.get_latest_version(rule_id)

                if latest_version and latest_version["hash"] != current_hash:
                    changes["updated"].append(rule_id)
                else:
                    changes["unchanged"].append(rule_id)

        return changes

    def bulk_record(self, rules: list[dict[str, Any]]) -> None:
        """
        Record versions for multiple rules.

        Args:
            rules: List of rule definitions
        """
        # Detect changes first
        changes = self.detect_changes(rules)

        # Record each rule
        for rule in rules:
            rule_id = rule.get("ruleID")

            if rule_id in changes["created"]:
                self.record_rule(rule, "create")
            elif rule_id in changes["updated"]:
                self.record_rule(rule, "update")

        # Record deletions
        for rule_id in changes["deleted"]:
            self.versions[rule_id].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "change_type": "delete",
                    "version": len(self.versions[rule_id]) + 1,
                }
            )

        logger.info(
            "Bulk record: %d created, %d updated, %d deleted",
            len(changes["created"]),
            len(changes["updated"]),
            len(changes["deleted"]),
        )

    def get_stats(self) -> dict[str, Any]:
        """
        Get versioning statistics.

        Returns:
            Statistics dictionary
        """
        total_rules = len(self.versions)
        total_versions = sum(len(history) for history in self.versions.values())

        # Rules by change frequency
        change_counts = {rule_id: len(history) for rule_id, history in self.versions.items()}

        most_changed = sorted(change_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_rules": total_rules,
            "total_versions": total_versions,
            "avg_versions_per_rule": round(total_versions / total_rules, 2) if total_rules else 0,
            "most_changed": most_changed,
        }
