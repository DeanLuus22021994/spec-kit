# Metadata Package

Validation rules for YAML metadata blocks and anchor patterns.

## Overview

This package contains rules that enforce proper metadata block structure and YAML anchor/alias usage across all configuration files.

## Rule Files

### metadata-block.yaml (8 rules)

Enforces proper metadata block structure:

- **yaml-metadata-block-required** (mandatory, effort 3) - All .config YAML files must have metadata block
- **yaml-metadata-anchor-required** (mandatory, effort 1) - Metadata must use &metadata anchor
- **yaml-metadata-merge-required** (mandatory, effort 1) - Must include <<: \*metadata merge key
- **yaml-metadata-version-quoted** (mandatory, effort 1) - Version numbers must be quoted
- **yaml-metadata-category-valid** (mandatory, effort 1) - Category must be valid value
- **yaml-metadata-keywords-array** (optional, effort 2) - Keywords should be array format
- **yaml-metadata-dates-iso8601** (optional, effort 1) - Use ISO 8601 date format

### anchors.yaml (6 rules)

Enforces proper YAML anchor and alias usage:

- **yaml-anchor-before-use** (mandatory, effort 2) - Anchors must be defined before use
- **yaml-anchor-naming-convention** (optional, effort 1) - Use descriptive anchor names
- **yaml-merge-key-alignment** (mandatory, effort 1) - Merge keys properly aligned
- **yaml-anchor-documentation** (optional, effort 1) - Document complex anchors
- **yaml-unused-anchor-detection** (potential, effort 1) - Detect unused anchors
- **yaml-cross-file-anchor-limitation** (potential, effort 3) - Warn about cross-file limitations

## Package Statistics

- **Total Rules**: 14
- **Mandatory Rules**: 7
- **Optional Rules**: 5
- **Potential Rules**: 2
- **Average Effort**: 1.4

## Usage

### Validate with full metadata package:

```bash
make validate-profile profile=strict package=metadata
```

### Run individual rule files:

```bash
kantra analyze --rules=metadata-block.yaml
kantra analyze --rules=anchors.yaml
```

### Quick validation:

```bash
make validate-rules-test package=metadata
```

## Rule Categories

- **metadata**: 8 rules
- **anchors**: 6 rules

## Testing

Test fixtures and unit tests are located in:

- `tests/fixtures/` - Sample YAML files for testing
- Run tests: `make validate-rules-test package=metadata`

## Dependencies

No external package dependencies.

## Related Documentation

- [YAML Best Practices](../../yaml-best-practices.yml#metadata_blocks)
- [Metadata Block Requirements](../../yaml-best-practices.yml#anchors_and_aliases)
- [Naming Conventions](../../naming-conventions.yml#anchors)
