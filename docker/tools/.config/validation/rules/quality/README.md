# Quality Package

Validation rules for YAML code quality, including duplicate detection, unused element identification, naming conventions, and performance monitoring.

## Overview

This package contains rules that improve YAML maintainability, detect potential errors, enforce consistent naming, and monitor file size and complexity.

## Rule Files

### duplicates.yaml (2 rules)

Detects duplicate elements:

- **yaml-duplicate-keys** (mandatory, effort 1) - Detect duplicate keys in same mapping
- **yaml-duplicate-anchors** (mandatory, effort 1) - Detect duplicate anchor names in document

### unused.yaml (2 rules)

Identifies unused elements:

- **yaml-unused-anchors** (optional, effort 1) - Detect anchors defined but never referenced
- **yaml-unused-merge-keys** (potential, effort 2) - Detect ineffective merge key usage

### naming.yaml (4 rules)

Enforces naming conventions:

- **yaml-key-naming-kebab-case** (optional, effort 1) - Recommend kebab-case for keys
- **yaml-key-naming-consistency** (optional, effort 2) - Detect mixed naming styles in file
- **yaml-anchor-naming-descriptive** (optional, effort 1) - Encourage descriptive anchor names
- **yaml-environment-variable-naming** (optional, effort 1) - Validate UPPER_SNAKE_CASE for env vars

### performance.yaml (4 rules)

Monitors size and complexity:

- **yaml-file-size-large** (potential, effort 5) - Warn on files >1000 lines
- **yaml-deep-nesting-complexity** (potential, effort 5) - Warn on nesting >6 levels
- **yaml-large-sequence-performance** (potential, effort 7) - Warn on sequences >100 items
- **yaml-complex-anchor-references** (potential, effort 3) - Warn on complex merge key usage

## Package Statistics

- **Total Rules**: 12
- **Mandatory Rules**: 2
- **Optional Rules**: 6
- **Potential Rules**: 4
- **Average Effort**: 2.4

## Usage

### Validate with full quality package:

```bash
make validate-profile profile=recommended package=quality
```

### Run individual rule files:

```bash
kantra analyze --rules=duplicates.yaml
kantra analyze --rules=unused.yaml
kantra analyze --rules=naming.yaml
kantra analyze --rules=performance.yaml
```

### Quick validation:

```bash
make validate-rules-test package=quality
```

## Rule Categories

- **duplicates**: 2 rules (mandatory - catch errors)
- **unused**: 2 rules (optional/potential - cleanup)
- **naming**: 4 rules (optional - consistency)
- **performance**: 4 rules (potential - warnings)

## Testing

Test fixtures and unit tests are located in:

- `tests/fixtures/` - Sample YAML files with quality issues for testing
- Run tests: `make validate-rules-test package=quality`

## Dependencies

No external package dependencies.

## Related Documentation

- [YAML Best Practices](../../yaml-best-practices.yml#code_quality)
- [YAML Spec - Node Comparison](https://yaml.org/spec/1.2/spec.html#id2765878)
- [YAML Anchors and Aliases](https://yaml.org/spec/1.2/spec.html#id2785586)

## Notes

Quality rules focus on maintainability and catching potential errors. Most are optional or potential (warnings), not mandatory, allowing flexibility while encouraging best practices.
