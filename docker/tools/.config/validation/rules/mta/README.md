# MTA Package

Validation rules for MTA 7.2 rule structure, labels, providers, conditions, and variables.

## Overview

This package contains rules that ensure MTA rulesets conform to the MTA 7.2 specification, including proper rule structure, label conventions, provider usage, condition logic, and variable management.

## Rule Files

### structure.yaml (5 rules)

Validates MTA rule structure and required fields:

- **mta-rule-required-fields** (mandatory, effort 1) - Ensure ruleID, description, message are present
- **mta-rule-id-pattern** (mandatory, effort 1) - Validate ruleID uses kebab-case format
- **mta-description-quality** (optional, effort 2) - Ensure descriptions are clear and detailed (50+ chars)
- **mta-message-template-quality** (optional, effort 2) - Ensure messages are actionable and helpful
- **mta-effort-values-valid** (mandatory, effort 1) - Validate effort uses standard values (0,1,3,5,7,13)

### labels.yaml (4 rules)

Validates MTA label usage:

- **mta-labels-reserved-konveyor** (mandatory, effort 1) - Proper use of konveyor.io/ namespace
- **mta-labels-format-valid** (optional, effort 1) - Labels follow key=value or simple tag format
- **mta-labels-category-values** (optional, effort 1) - Category labels use standard values
- **mta-labels-usage-guidelines** (optional, effort 1) - Rules have meaningful labels (not empty)

### providers.yaml (4 rules)

Validates builtin provider usage:

- **mta-provider-builtin-file** (mandatory, effort 1) - builtin.file has required pattern field
- **mta-provider-builtin-filecontent** (mandatory, effort 2) - builtin.filecontent has pattern and filePattern
- **mta-provider-language-specific** (optional, effort 3) - Language providers (java, go, dotnet) properly configured
- **mta-provider-pattern-quality** (optional, effort 2) - Patterns are specific, not overly broad (.\*)

### conditions.yaml (5 rules)

Validates when condition logic:

- **mta-when-condition-structure** (mandatory, effort 2) - when field properly structured with provider or operator
- **mta-or-operator-usage** (mandatory, effort 1) - or operator has 2+ conditions in array
- **mta-and-operator-usage** (mandatory, effort 1) - and operator has 2+ conditions in array
- **mta-not-operator-usage** (mandatory, effort 1) - not operator wraps single condition (not array)
- **mta-condition-complexity** (potential, effort 5) - Warn on deep nesting (3+ levels)

### variables.yaml (6 rules)

Validates customVariables and categories:

- **mta-custom-variables-pattern** (optional, effort 2) - Messages with {{var}} have customVariables defined
- **mta-custom-variables-naming** (optional, effort 1) - Variable names use camelCase
- **mta-custom-variables-validation** (mandatory, effort 2) - All {{variables}} in messages are defined
- **mta-category-values** (mandatory, effort 1) - Category uses standard values (mandatory/optional/potential)
- **mta-category-effort-alignment** (potential, effort 3) - Category and effort appropriately aligned
- **mta-category-label-consistency** (mandatory, effort 1) - category field matches category= label

## Package Statistics

- **Total Rules**: 24
- **Mandatory Rules**: 13
- **Optional Rules**: 9
- **Potential Rules**: 2
- **Average Effort**: 1.5

## Usage

### Validate with full MTA package:

```bash
make validate-profile profile=strict package=mta
```

### Run individual rule files:

```bash
kantra analyze --rules=structure.yaml
kantra analyze --rules=labels.yaml
kantra analyze --rules=providers.yaml
kantra analyze --rules=conditions.yaml
kantra analyze --rules=variables.yaml
```

### Quick validation:

```bash
make validate-rules-test package=mta
```

## Rule Categories

- **structure**: 5 rules (3 mandatory, 2 optional)
- **labels**: 4 rules (1 mandatory, 3 optional)
- **providers**: 4 rules (2 mandatory, 2 optional)
- **conditions**: 5 rules (4 mandatory, 1 potential)
- **variables**: 6 rules (3 mandatory, 2 optional, 1 potential)

## Testing

Test fixtures and unit tests are located in:

- `tests/fixtures/` - Sample MTA ruleset files for testing
- Run tests: `make validate-rules-test package=mta`

## Dependencies

No external package dependencies.

## Related Documentation

- [MTA Rule Documentation](https://github.com/konveyor/analyzer-lsp/blob/main/docs/rules.md)
- [MTA Provider Documentation](https://github.com/konveyor/analyzer-lsp/blob/main/docs/providers.md)
- [YAML Best Practices](../../yaml-best-practices.yml#mta_rules)

## Notes

This package validates MTA ruleset structure itself, not the YAML syntax. Use the `syntax` package for YAML formatting validation.
