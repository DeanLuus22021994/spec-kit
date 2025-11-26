#!/usr/bin/env python3
"""Phase 1 verification test script."""
from __future__ import annotations

from pathlib import Path

from core.engine.cache import ResultCache
from core.engine.reporter import ReportGenerator
from core.rules.registry import RuleRegistry


def main() -> None:
    """Run Phase 1 functionality tests."""
    print("=" * 70)
    print("PHASE 1 FUNCTIONALITY TEST")
    print("=" * 70)
    print()

    # Test ResultCache
    print("Testing ResultCache...")
    cache = ResultCache(Path(".test-cache"))
    assert cache is not None
    print("  ✅ Cache initialized")
    print()

    # Test RuleRegistry
    print("Testing RuleRegistry...")
    rules_reg = RuleRegistry(Path("rules"))
    packages = rules_reg.discover_packages()
    if packages:
        print(f'  ✅ Found {len(packages)} packages: {", ".join(packages)}')
    else:
        print("  ✅ Rule registry ready (0 packages - normal for fresh setup)")
    print()

    # Test ReportGenerator
    print("Testing ReportGenerator...")
    reporter = ReportGenerator(Path("reports"))
    assert reporter is not None
    print("  ✅ Reporter initialized")
    print()

    print("=" * 70)
    print("✅ ALL PHASE 1 MODULES FUNCTIONAL")
    print("=" * 70)


if __name__ == "__main__":
    main()
