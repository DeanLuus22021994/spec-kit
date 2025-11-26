# Structure Package

Validation rules for YAML file organization and documentation.

## Overview

This package contains rules that enforce proper file structure, section ordering, and documentation practices.

## Rule Files

### organization.yaml (9 rules)

Enforces file organization standards:

- **yaml-file-header-comment** (optional, effort 1) - Descriptive header comments
- **yaml-metadata-block-first** (mandatory, effort 3) - Metadata block placement
- **yaml-anchors-before-content** (optional, effort 2) - Anchor definition placement
- **yaml-section-separation** (optional, effort 1) - Blank lines between sections
- **yaml-cross-references-section** (optional, effort 2) - Include cross-references
- **yaml-related-documentation-last** (optional, effort 1) - Documentation section last
- **yaml-alphabetical-sections** (optional, effort 2) - Consistent section ordering
- **yaml-consistent-naming** (optional, effort 2) - Consistent key naming
- **yaml-inline-comments-alignment** (optional, effort 1) - Aligned inline comments

## Package Statistics

- **Total Rules**: 9
- **Mandatory Rules**: 2
- **Optional Rules**: 7
- **Average Effort**: 1.7

## Usage

### Validate with full structure package:

```bash
make validate-profile profile=strict package=structure
```

### Run organization rules:

```bash
kantra analyze --rules=organization.yaml
```

### Quick validation:

```bash
make validate-rules-test package=structure
```

## Rule Categories

- **file_organization**: 9 rules

## Testing

Test fixtures and unit tests are located in:

- `tests/fixtures/` - Sample YAML files for testing
- Run tests: `make validate-rules-test package=structure`

## Dependencies

- **metadata** package - Required for metadata-block validation

## Related Documentation

- [YAML Best Practices](../../yaml-best-practices.yml#file_organization)
- [Naming Conventions](../../naming-conventions.yml)
- [Comment Guidelines](../../yaml-best-practices.yml#comments)
