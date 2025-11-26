#!/usr/bin/env python3
"""
Rule Assertions
Custom assertion helpers for rule testing.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RuleAssertions:
    """
    Custom assertions for validation rule testing.

    Provides helper methods for common rule test assertions.
    """

    @staticmethod
    def assert_rule_matches(rule_result: dict[str, Any], expected_matches: int) -> bool:
        """
        Assert rule matched expected number of times.

        Args:
            rule_result: Rule execution result
            expected_matches: Expected match count

        Returns:
            True if assertion passes

        Raises:
            AssertionError: If assertion fails
        """
        actual_matches = len(rule_result.get("matches", []))

        if actual_matches != expected_matches:
            raise AssertionError(f"Expected {expected_matches} matches, got {actual_matches}")

        return True

    @staticmethod
    def assert_no_matches(rule_result: dict[str, Any]) -> bool:
        """
        Assert rule did not match.

        Args:
            rule_result: Rule execution result

        Returns:
            True if assertion passes
        """
        return RuleAssertions.assert_rule_matches(rule_result, 0)

    @staticmethod
    def assert_message_contains(rule_result: dict[str, Any], expected_text: str) -> bool:
        """
        Assert rule message contains expected text.

        Args:
            rule_result: Rule execution result
            expected_text: Expected text in message

        Returns:
            True if assertion passes
        """
        message = rule_result.get("message", "")

        if expected_text not in message:
            raise AssertionError(f"Expected message to contain '{expected_text}', " f"got: {message}")

        return True

    @staticmethod
    def assert_category(rule_result: dict[str, Any], expected_category: str) -> bool:
        """
        Assert rule has expected category.

        Args:
            rule_result: Rule execution result
            expected_category: Expected category

        Returns:
            True if assertion passes
        """
        actual_category = rule_result.get("category")

        if actual_category != expected_category:
            raise AssertionError(f"Expected category '{expected_category}', " f"got: {actual_category}")

        return True

    @staticmethod
    def assert_effort(rule_result: dict[str, Any], expected_effort: int) -> bool:
        """
        Assert rule has expected effort level.

        Args:
            rule_result: Rule execution result
            expected_effort: Expected effort (0, 1, 3, 5, 7, 13)

        Returns:
            True if assertion passes
        """
        actual_effort = rule_result.get("effort")

        if actual_effort != expected_effort:
            raise AssertionError(f"Expected effort {expected_effort}, got: {actual_effort}")

        return True

    @staticmethod
    def assert_line_number(rule_result: dict[str, Any], expected_line: int) -> bool:
        """
        Assert rule matched at expected line number.

        Args:
            rule_result: Rule execution result
            expected_line: Expected line number

        Returns:
            True if assertion passes
        """
        matches = rule_result.get("matches", [])

        if not matches:
            raise AssertionError("No matches found")

        line_numbers = [m.get("lineNumber") for m in matches]

        if expected_line not in line_numbers:
            raise AssertionError(f"Expected match at line {expected_line}, " f"found at: {line_numbers}")

        return True
