# Archived Obsolete Configurations

This directory contains configuration files that have been superseded by the centralized `.config/` YAML-based configuration system.

## Archived Files

| File                         | Original Location              | Reason                                                                                | Archived Date |
| ---------------------------- | ------------------------------ | ------------------------------------------------------------------------------------- | ------------- |
| `runner-config-template.txt` | `infrastructure/runner/config` | Duplicated in `.config/services.yml` runner section; template with placeholder values | 2025-11-25    |

## Migration Notes

All configuration is now centralized in:

- `.config/services.yml` - Service definitions, resources, tiers
- `.config/gpu-resources.yml` - GPU/VRAM partitioning
- `.config/optimization-toggles.yml` - Real-time toggles
- `.config/infrastructure.yml` - Network, security, logging
- `.config/tracing.yml` - Agent tracing and observability

## Do Not Delete

These files are archived for reference. The centralized YAML configs in `.config/` are the source of truth.
