#!/usr/bin/env python3
"""Profile Command.

Manage validation profiles.
"""

from __future__ import annotations

import logging
import os
import subprocess
import traceback
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def manage_profiles(
    action: str,
    profile_name: str | None,
    output_path: Path | None,
    verbose: bool,
) -> int:
    """Manage validation profiles.

    Args:
        action: Action to perform (list, show, create, edit).
        profile_name: Profile name.
        output_path: Output file path.
        verbose: Verbose output.

    Returns:
        Exit code.
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        profiles_dir = project_root / "tools" / ".config" / "validation" / "profiles"

        if action == "list":
            return list_profiles(profiles_dir)

        # Actions requiring profile_name
        if not profile_name:
            logger.error("Profile name required for '%s' action", action)
            return 1

        if action == "show":
            return show_profile(profiles_dir, profile_name)
        if action == "create":
            return create_profile(profiles_dir, profile_name, output_path)
        if action == "edit":
            return edit_profile(profiles_dir, profile_name)

        logger.error("Unknown action: %s", action)
        return 1

    except (OSError, ValueError, yaml.YAMLError) as e:
        logger.error("Profile management failed: %s", e)
        if verbose:
            traceback.print_exc()
        return 1


def list_profiles(profiles_dir: Path) -> int:
    """List all available profiles.

    Args:
        profiles_dir: Directory containing profile YAML files.

    Returns:
        Exit code.
    """
    print("\nAvailable Profiles:")
    print("=" * 60)

    if not profiles_dir.exists():
        print("No profiles found")
        return 0

    profile_files = sorted(profiles_dir.glob("*.yaml"))

    for profile_file in profile_files:
        profile_name = profile_file.stem

        try:
            with open(profile_file, "r", encoding="utf-8") as f:
                profile = yaml.safe_load(f) or {}

            description = profile.get("description", "No description")
            enabled_packages = profile.get("enabledPackages", [])

            print(f"\n{profile_name}")
            print(f"  Description: {description}")
            print(f"  Packages: {len(enabled_packages)}")

        except (OSError, yaml.YAMLError) as e:
            logger.warning("Failed to load profile %s: %s", profile_name, e)

    print("\n" + "=" * 60 + "\n")
    return 0


def show_profile(profiles_dir: Path, profile_name: str) -> int:
    """Show detailed profile information.

    Args:
        profiles_dir: Directory containing profile YAML files.
        profile_name: Name of the profile to show.

    Returns:
        Exit code.
    """
    profile_path = profiles_dir / f"{profile_name}.yaml"

    if not profile_path.exists():
        logger.error("Profile not found: %s", profile_name)
        return 1

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f) or {}

        print("\n" + "=" * 60)
        print(f"PROFILE: {profile_name}")
        print("=" * 60)

        print(f"\nDescription: {profile.get('description', 'N/A')}")

        enabled_packages = profile.get("enabledPackages", [])
        print(f"\nEnabled Packages ({len(enabled_packages)}):")
        for package in enabled_packages:
            print(f"  - {package}")

        disabled_rules = profile.get("disabledRules", [])
        if disabled_rules:
            print(f"\nDisabled Rules ({len(disabled_rules)}):")
            for rule in disabled_rules:
                print(f"  - {rule}")

        custom_config = profile.get("customConfig", {})
        if custom_config:
            print("\nCustom Configuration:")
            print(yaml.dump(custom_config, default_flow_style=False, indent=2))

        print("\n" + "=" * 60 + "\n")
        return 0

    except (OSError, yaml.YAMLError) as e:
        logger.error("Failed to show profile: %s", e)
        return 1


def create_profile(
    profiles_dir: Path,
    profile_name: str,
    output_path: Path | None,
) -> int:
    """Create a new profile.

    Args:
        profiles_dir: Directory for profile YAML files.
        profile_name: Name for the new profile.
        output_path: Optional custom output path.

    Returns:
        Exit code.
    """
    profiles_dir.mkdir(parents=True, exist_ok=True)

    profile_path = output_path or (profiles_dir / f"{profile_name}.yaml")

    if profile_path.exists():
        logger.warning("Profile already exists: %s", profile_path)
        overwrite = input("Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            return 0

    # Interactive profile creation
    print(f"\nCreating profile: {profile_name}")
    description = input("Description: ").strip()

    print("\nAvailable packages:")
    packages_dir = profiles_dir.parent / "packages"
    available_packages = []

    if packages_dir.exists():
        for pkg_dir in sorted(packages_dir.iterdir()):
            if pkg_dir.is_dir():
                available_packages.append(pkg_dir.name)
                print(f"  - {pkg_dir.name}")

    print("\nEnter packages to enable (comma-separated):")
    enabled_input = input("> ").strip()
    enabled_packages = [p.strip() for p in enabled_input.split(",") if p.strip()]

    # Create profile
    profile = {
        "name": profile_name,
        "description": description or f"Custom profile: {profile_name}",
        "enabledPackages": enabled_packages,
        "disabledRules": [],
        "customConfig": {},
    }

    # Write profile
    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(profile, f, default_flow_style=False, sort_keys=False)

    logger.info("Created profile: %s", profile_path)
    return 0


def edit_profile(profiles_dir: Path, profile_name: str) -> int:
    """Edit an existing profile.

    Args:
        profiles_dir: Directory containing profile YAML files.
        profile_name: Name of the profile to edit.

    Returns:
        Exit code.
    """
    profile_path = profiles_dir / f"{profile_name}.yaml"

    if not profile_path.exists():
        logger.error("Profile not found: %s", profile_name)
        return 1

    # Open in default editor

    editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "nano")

    try:
        subprocess.run([editor, str(profile_path)], check=False)
        logger.info("Edited profile: %s", profile_path)
        return 0
    except (OSError, subprocess.SubprocessError) as e:
        logger.error("Failed to edit profile: %s", e)
        return 1
