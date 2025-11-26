# Syntax Package

Validation rules for YAML indentation, quoting, and multiline string syntax.

## Overview

This package contains rules that enforce 2-space indentation, proper alignment, correct string quoting practices, and proper multiline string formatting.

## Rule Files

### indentation.yaml (7 rules)

Enforces consistent indentation:

- **yaml-no-tabs-indentation** (mandatory, effort 1) - No tabs, spaces only
- **yaml-two-space-indentation** (mandatory, effort 2) - Use 2 spaces per level
- **yaml-list-alignment** (mandatory, effort 1) - List items properly aligned
- **yaml-nested-structure-alignment** (mandatory, effort 2) - Nested structures consistent
- **yaml-multiline-string-indentation** (mandatory, effort 2) - Multiline strings indented
- **yaml-flow-style-spacing** (optional, effort 1) - Flow collections properly spaced

### quoting.yaml (7 rules)

Enforces proper quoting practices:

- **yaml-version-numbers-quoted** (mandatory, effort 1) - Quote version numbers
- **yaml-boolean-values-unquoted** (optional, effort 1) - Unquote booleans
- **yaml-special-characters-quoted** (mandatory, effort 2) - Quote special characters
- **yaml-escape-sequences-double-quotes** (mandatory, effort 1) - Use double quotes for escapes
- **yaml-url-quoting** (mandatory, effort 1) - Quote URLs
- **yaml-simple-values-unquoted** (optional, effort 1) - Don't quote simple values
- **yaml-regex-patterns-quoted** (optional, effort 1) - Use single quotes for regex

### multiline.yaml (8 rules)

Enforces proper multiline string formatting:

- **yaml-literal-block-indicator** (optional, effort 1) - Use literal block (|) for preserving newlines
- **yaml-folded-block-indicator** (optional, effort 1) - Use folded block (>) for wrapping text
- **yaml-block-chomping-strip** (optional, effort 1) - Strip chomping (|-) removes trailing newlines
- **yaml-block-chomping-keep** (optional, effort 1) - Keep chomping (|+) preserves trailing newlines
- **yaml-block-content-indentation** (mandatory, effort 2) - Content must be indented consistently
- **yaml-block-indicator-positioning** (mandatory, effort 1) - Block indicators properly positioned
- **yaml-multiline-empty-lines** (optional, effort 1) - Empty lines should be completely empty
- **yaml-multiline-trailing-whitespace** (optional, effort 1) - Avoid trailing whitespace

### collections.yaml (6 rules)

Enforces proper collection formatting:

- **yaml-block-vs-flow-style** (optional, effort 2) - Use block style for complex, flow for simple collections
- **yaml-nested-collection-depth** (potential, effort 5) - Warn on deep nesting (6+ levels)
- **yaml-compact-mapping** (optional, effort 1) - Use compact mappings for simple key-value pairs
- **yaml-sequence-alignment** (mandatory, effort 2) - Sequence items properly aligned
- **yaml-flow-collection-spacing** (optional, effort 1) - Proper spacing in flow collections
- **yaml-mixed-collection-style** (optional, effort 2) - Avoid mixing block and flow styles

### comments.yaml (5 rules)

Enforces proper comment placement and documentation:

- **yaml-comment-positioning** (optional, effort 1) - Comments on own line, not inline
- **yaml-header-comment-structure** (optional, effort 2) - File header comments for documentation
- **yaml-section-documentation** (optional, effort 2) - Document major sections
- **yaml-multiline-documentation** (optional, effort 2) - Use multiline comments for complex docs
- **yaml-comment-alignment** (optional, effort 1) - Align comments at consistent column

## Package Statistics

- **Total Rules**: 33
- **Mandatory Rules**: 14
- **Optional Rules**: 18
- **Potential Rules**: 1
- **Average Effort**: 1.3

## Usage

### Validate with full syntax package:

```bash
make validate-profile profile=strict package=syntax
```

### Run individual rule files:

```bash
kantra analyze --rules=indentation.yaml
kantra analyze --rules=quoting.yaml
kantra analyze --rules=multiline.yaml
kantra analyze --rules=collections.yaml
kantra analyze --rules=comments.yaml
```

### Quick validation:

```bash
make validate-rules-test package=syntax
```

## Rule Categories

- **indentation**: 7 rules
- **quoting**: 7 rules
- **multiline**: 8 rules
- **collections**: 6 rules
- **comments**: 5 rules

## Testing

Test fixtures and unit tests are located in:

- `tests/fixtures/` - Sample YAML files for testing
- Run tests: `make validate-rules-test package=syntax`

## Dependencies

No external package dependencies.

## Related Documentation

- [YAML Best Practices](../../yaml-best-practices.yml#indentation)
- [YAML Best Practices](../../yaml-best-practices.yml#quoting)
- [Multiline Strings](../../yaml-best-practices.yml#multiline_strings)
- [Collections](../../yaml-best-practices.yml#collections)
- [Comments](../../yaml-best-practices.yml#comments)
