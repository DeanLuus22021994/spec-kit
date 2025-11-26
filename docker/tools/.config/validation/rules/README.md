# Red Hat MTA YAML Rules - Usage Guide

## Overview

This directory contains custom YAML validation rules for the Red Hat Migration Toolkit for Applications (MTA) 7.2 / Kantra CLI. These rules enforce the YAML best practices defined in `../../../.config/copilot/yaml-best-practices.yml` across the entire repository.

**Location:** `tools/.config/validation/rules/`

## Ruleset Structure

```
tools/.config/validation/rules/
├── ruleset.yaml                      # Ruleset metadata and configuration
├── metadata-validation.yaml          # Metadata block rules (7 rules)
├── anchor-pattern-validation.yaml    # Anchor/alias rules (6 rules)
├── indentation-validation.yaml       # Indentation rules (6 rules)
├── quoting-validation.yaml           # String quoting rules (7 rules)
├── file-organization-validation.yml  # File structure rules (9 rules)
└── README.md                         # This file
```

## Rule Categories

### Metadata Validation (7 rules)

- **yaml-metadata-block-required**: Enforce metadata block presence
- **yaml-metadata-anchor-required**: Require `&metadata` anchor definition
- **yaml-metadata-merge-required**: Require `<<: *metadata` merge key
- **yaml-metadata-version-quoted**: Enforce quoted version numbers
- **yaml-metadata-category-valid**: Validate category values
- **yaml-metadata-keywords-array**: Ensure keywords is array format

### Anchor Pattern Validation (6 rules)

- **yaml-anchor-before-use**: Anchors defined before aliases
- **yaml-anchor-naming-convention**: Descriptive anchor names
- **yaml-merge-key-alignment**: Proper merge key indentation
- **yaml-anchor-documentation**: Comment complex anchors
- **yaml-unused-anchor-detection**: Detect unused anchors
- **yaml-cross-file-anchor-limitation**: Warn about cross-file limitations

### Indentation Validation (6 rules)

- **yaml-no-tabs-indentation**: No tabs, only spaces
- **yaml-two-space-indentation**: Consistent 2-space indentation
- **yaml-list-alignment**: Proper list item alignment
- **yaml-nested-structure-alignment**: Consistent nesting
- **yaml-multiline-string-indentation**: Multiline content indentation
- **yaml-flow-style-spacing**: Flow collection spacing

### Quoting Validation (7 rules)

- **yaml-version-numbers-quoted**: Quote all version numbers
- **yaml-boolean-values-unquoted**: Unquote boolean values
- **yaml-special-characters-quoted**: Quote special characters
- **yaml-escape-sequences-double-quotes**: Double quotes for escapes
- **yaml-url-quoting**: Quote URLs
- **yaml-simple-values-unquoted**: Unquote simple values
- **yaml-regex-patterns-quoted**: Single quotes for regex

### File Organization Validation (9 rules)

- **yaml-file-header-comment**: Descriptive header comment
- **yaml-metadata-block-first**: Metadata as first element
- **yaml-anchors-before-content**: Anchors before content
- **yaml-section-separation**: Blank lines between sections
- **yaml-cross-references-section**: Include cross-references
- **yaml-related-documentation-last**: Documentation section last
- **yaml-alphabetical-sections**: Logical section ordering
- **yaml-consistent-naming**: Consistent key naming
- **yaml-inline-comments-alignment**: Aligned inline comments

## Running Analysis

**Note:** This ruleset uses Kantra CLI, the unified tool for MTA 7.2. All commands use `kantra analyze` instead of legacy `mta-cli`.

### Quick Start with Automation Script

```bash
# From repository root - uses containerized Kantra
make validate-yaml

# Mandatory rules only
make validate-yaml-mandatory

# View HTML report
make validate-yaml-report
```

### Direct Kantra CLI Usage

#### Analyze Single File

```bash
kantra analyze \
  --input /path/to/file.yml \
  --output ./.config/validation/reports/ \
  --rules ./tools/.config/validation/rules/ \
  --enable-default-rulesets=false \
  --run-local
```

#### Analyze Entire Repository

```bash
kantra analyze \
  --input . \
  --output ./tools/.config/validation/reports/ \
  --rules ./tools/.config/validation/rules/ \
  --enable-default-rulesets=false \
  --label-selector="category=mandatory" \
  --run-local
```

### Filter by Severity

```bash
# Mandatory rules only
kantra analyze \
  --input . \
  --output ./tools/.config/validation/reports/ \
  --rules ./tools/.config/validation/rules/ \
  --label-selector="category=mandatory" \
  --enable-default-rulesets=false

# Optional rules only
kantra analyze \
  --input . \
  --output ./tools/.config/validation/reports/ \
  --rules ./tools/.config/validation/rules/ \
  --label-selector="category=optional" \
  --enable-default-rulesets=false

# Potential issues only
kantra analyze \
  --input . \
  --output ./tools/.config/validation/reports/ \
  --rules ./tools/.config/validation/rules/ \
  --label-selector="category=potential" \
  --enable-default-rulesets=false
```

### Filter by Rule Type

```bash
# Metadata rules only
kantra analyze \
  --input . \
  --output ./tools/.config/validation/reports/ \
  --rules ./tools/.config/validation/rules/metadata-validation.yaml \
  --enable-default-rulesets=false

# Indentation rules only
kantra analyze \
  --input . \
  --output ./tools/.config/validation/reports/ \
  --rules ./tools/.config/validation/rules/indentation-validation.yaml \
  --enable-default-rulesets=false
```

## Viewing Reports

After analysis completes, open the HTML report:

```bash
# Windows
start ./tools/.config/validation/reports/static-report/index.html

# Linux/macOS
open ./tools/.config/validation/reports/static-report/index.html

# Or use make target
make validate-yaml-report
```

## Rule Effort Levels

- **Effort 1**: Quick fix (< 5 minutes)

  - Quote a version number
  - Remove unnecessary quotes
  - Add missing anchor

- **Effort 2**: Moderate fix (5-15 minutes)

  - Fix indentation throughout file
  - Reorganize sections
  - Add cross-references

- **Effort 3**: Substantial fix (15-30 minutes)
  - Add complete metadata block
  - Restructure entire file
  - Implement anchor pattern across file

## Rule Categories

### Mandatory

Must be fixed for successful validation. These represent critical best practices that prevent parsing errors or semantic issues.

### Optional

Should be fixed for optimal quality. These improve readability, maintainability, and consistency.

### Potential

Review during cleanup. These may indicate issues but require human judgment to determine necessity.

## Integration with CI/CD

### GitHub Actions Workflow

```yaml
name: YAML Validation

on: [push, pull_request]

jobs:
  validate-yaml:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install MTA CLI
        run: |
          curl -LO https://github.com/konveyor/analyzer-lsp/releases/download/v0.4.0/mta-cli-linux-amd64
          chmod +x mta-cli-linux-amd64
          sudo mv mta-cli-linux-amd64 /usr/local/bin/mta-cli

      - name: Run YAML Validation
        run: |
          mta-cli analyze \
            --input . \
            --output ./output/ \
            --rules ./custom-rules/ \
            --label-selector="category=mandatory"

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: mta-report
          path: ./output/static-report/
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: mta-yaml-validation
      name: MTA YAML Validation
      entry: mta-cli analyze --input . --output /tmp/mta-output --rules ./custom-rules/ --label-selector="category=mandatory"
      language: system
      types: [yaml]
      pass_filenames: false
```

## Rule Customization

### Adding New Rules

1. Create new rule file in `custom-rules/`
2. Follow MTA YAML rule structure:

```yaml
- ruleID: unique-rule-id
  description: |
    Detailed description of what the rule checks.
  labels:
    - "konveyor.io/source=yaml"
    - "konveyor.io/target=yaml-best-practices"
    - "category=mandatory"
  when:
    builtin.filecontent:
      filePattern: ".*\\.ya?ml$"
      pattern: "regex pattern to match"
  customVariables:
    - pattern: "(capture group)"
      name: variableName
  message: |
    Message shown when rule matches.
    Can use {{ variableName }} from customVariables.
  effort: 1
  category: mandatory
  links:
    - url: "https://docs.example.com"
      title: "Reference Documentation"
```

3. Add rule file to `ruleset.yaml`:

```yaml
rules:
  - metadata-validation.yaml
  - anchor-pattern-validation.yaml
  - your-new-rule.yaml
```

### Modifying Existing Rules

1. Edit rule file directly
2. Test with sample violations
3. Update effort/category as needed
4. Document changes in commit message

## Best Practices Reference

All rules are based on standards defined in:

- `.config/copilot/yaml-best-practices.yml`
- Red Hat MTA 7.2 Rules Development Guide
- YAML 1.2 Specification

## Common Fixes

### Add Missing Metadata Block

```yaml
# Before
services:
  backend:
    port: 8080

# After
# Service Configuration
metadata: &metadata
  version: "1.0.0"
  category: "config"
  keywords: [services, configuration]

<<: *metadata

services:
  backend:
    port: 8080
```

### Fix Version Number Quoting

```yaml
# Before
version: 1.0.0

# After
version: "1.0.0"
```

### Implement Anchor Pattern

```yaml
# Before
metadata:
  version: "1.0.0"
  category: "config"

# After
metadata: &metadata
  version: "1.0.0"
  category: "config"

<<: *metadata
```

### Fix Indentation

```yaml
# Before (4 spaces)
services:
    backend:
        port: 8080

# After (2 spaces)
services:
  backend:
    port: 8080
```

## Troubleshooting

### No Issues Detected

- Verify rule patterns match your YAML structure
- Check label-selector filters aren't too restrictive
- Ensure `--enable-default-rulesets=false` is set

### Too Many False Positives

- Adjust rule patterns to be more specific
- Add filePattern filters to scope rules
- Change category from mandatory to optional

### Performance Issues

- Use filePattern to limit scope
- Run specific rule files instead of entire ruleset
- Exclude generated or vendor files

## Contributing

To contribute new rules or improvements:

1. Follow existing rule structure
2. Test thoroughly with sample files
3. Document in this README
4. Update ruleset.yaml
5. Submit pull request

## Resources

- [Red Hat MTA Documentation](https://docs.redhat.com/en/documentation/migration_toolkit_for_applications/7.2/html/rules_development_guide/creating-yaml-rules_rules-development-guide)
- [YAML 1.2 Specification](https://yaml.org/spec/1.2/spec.html)
- [Repository YAML Best Practices](.config/copilot/yaml-best-practices.yml)
- [Konveyor Project](https://www.konveyor.io/)

## License

These rules follow the same license as the parent repository.
