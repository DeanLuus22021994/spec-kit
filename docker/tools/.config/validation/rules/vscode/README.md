# VSCode Package

Validation rules for VSCode YAML extension compliance, JSON schemas, and custom tag configuration.

## Overview

This package contains rules that ensure proper configuration of the VSCode YAML extension (Red Hat), validate JSON schema definitions, and check custom YAML tag configuration.

## Rule Files

### compliance.yaml (3 rules)

Validates VSCode YAML extension settings:

- **vscode-yaml-schema-directive** (optional, effort 1) - YAML files in .vscode/ have schema directives
- **vscode-yaml-settings-schema** (optional, effort 2) - settings.json defines yaml.schemas associations
- **vscode-yaml-validation-enabled** (optional, effort 1) - yaml.validate and related settings enabled

### schemas.yaml (2 rules)

Validates JSON schema definitions:

- **vscode-custom-schema-valid-json** (mandatory, effort 1) - Custom schemas have $schema declaration
- **vscode-schema-documentation** (optional, effort 2) - Schemas include title, description, examples

### tags.yaml (2 rules)

Validates custom YAML tag configuration:

- **vscode-custom-tags-configuration** (optional, effort 1) - Custom tags (!tag) registered in settings.json
- **vscode-tag-format-valid** (mandatory, effort 1) - Tag format is "!tagName type" (type = scalar/sequence/mapping)

## Package Statistics

- **Total Rules**: 7
- **Mandatory Rules**: 2
- **Optional Rules**: 5
- **Average Effort**: 1.3

## Usage

### Validate with full VSCode package:

```bash
make validate-profile profile=development package=vscode
```

### Run individual rule files:

```bash
kantra analyze --rules=compliance.yaml
kantra analyze --rules=schemas.yaml
kantra analyze --rules=tags.yaml
```

### Quick validation:

```bash
make validate-rules-test package=vscode
```

## Rule Categories

- **compliance**: 3 rules (optional - IDE configuration)
- **schemas**: 2 rules (1 mandatory, 1 optional - schema validation)
- **tags**: 2 rules (1 mandatory, 1 optional - custom tag support)

## Testing

Test fixtures and unit tests are located in:

- `tests/fixtures/` - Sample VSCode settings, schemas, and YAML files for testing
- Run tests: `make validate-rules-test package=vscode`

## Dependencies

No external package dependencies.

## Related Documentation

- [VSCode YAML Extension](https://github.com/redhat-developer/vscode-yaml)
- [JSON Schema Store](https://www.schemastore.org/json/)
- [JSON Schema Guide](https://json-schema.org/understanding-json-schema/)
- [YAML Language Server Settings](https://github.com/redhat-developer/vscode-yaml#language-server-settings)

## Notes

This package is specific to VSCode/Red Hat YAML extension. Rules help configure the IDE for optimal YAML editing experience with IntelliSense, validation, and custom tag support.

Most rules are optional as they enhance development experience but aren't required for valid YAML.
