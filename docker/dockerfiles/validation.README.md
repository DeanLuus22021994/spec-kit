# YAML Validation Docker Service

Containerized YAML validation service using Kantra CLI and Red Hat MTA rules.

## Overview

The validation service provides isolated, reproducible YAML validation with:

- **Kantra CLI**: Red Hat MTA's unified analysis tool
- **Modular Rules**: 107 validation rules across 6 categories
- **Flexible Profiles**: 5 pre-configured validation profiles
- **Dual Modes**: Containerless (fast) and hybrid (isolated) execution
- **Persistent Reports**: Named volumes for validation artifacts

## Architecture

```
validation.Dockerfile
├── Stage 1: Extract Kantra binary from quay.io/konveyor/kantra:latest
└── Stage 2: Build validation container
    ├── Python 3.14-slim base
    ├── Podman installation (for hybrid mode)
    ├── Validation framework
    ├── Automation scripts
    └── Non-root user (toolsuser:1001)
```

## Quick Start

### Build and Run

```bash
# Build validation container
docker-compose -f docker-compose.validation.yml build

# Run with default profile (recommended)
docker-compose -f docker-compose.validation.yml run --rm validation

# Run with strict profile
docker-compose -f docker-compose.validation.yml run --rm validation --profile strict

# Run mandatory rules only
docker-compose -f docker-compose.validation.yml run --rm validation --mandatory
```

### Integrated Usage (with tools service)

```bash
# Run from tools directory
cd tools

# Run validation through integrated setup
docker-compose -f docker-compose.tools.yml run --rm validation

# Run with environment override
VALIDATION_PROFILE=ci-cd docker-compose -f docker-compose.tools.yml run --rm validation
```

## Configuration

### Environment Variables

| Variable             | Default       | Description                              |
| -------------------- | ------------- | ---------------------------------------- |
| `VALIDATION_PROFILE` | `recommended` | Profile: strict, recommended, minimal... |
| `RUN_MODE`           | `local`       | Mode: local (containerless) or hybrid    |
| `REPORT_FORMAT`      | `html,yaml`   | Output formats: html, yaml, json         |
| `LABEL_SELECTOR`     | (none)        | Filter rules by label                    |
| `FAIL_ON_WARNING`    | `false`       | Strict mode flag                         |

### Validation Profiles

#### Strict

Zero-tolerance validation with all rules enforced.

```bash
docker-compose -f docker-compose.validation.yml run --rm validation --profile strict
```

- **Rules**: All 107 rules active
- **Fail On**: Any violation
- **Use Case**: Pre-release validation, quality gates

#### Recommended (Default)

Balanced validation for general use.

```bash
docker-compose -f docker-compose.validation.yml run --rm validation
# or explicitly:
docker-compose -f docker-compose.validation.yml run --rm validation --profile recommended
```

- **Rules**: Mandatory + high-priority optional
- **Fail On**: Mandatory violations
- **Use Case**: Daily development, PR checks

#### Minimal

Fast validation with mandatory rules only.

```bash
docker-compose -f docker-compose.validation.yml run --rm validation --profile minimal
```

- **Rules**: Mandatory rules only
- **Fail On**: Mandatory violations
- **Use Case**: Quick local checks, pre-commit hooks

#### CI-CD

Optimized for continuous integration pipelines.

```bash
VALIDATION_PROFILE=ci-cd docker-compose -f docker-compose.validation.yml run --rm validation
```

- **Rules**: Mandatory + CI-critical optional
- **Fail On**: CI-blocking issues
- **Use Case**: GitHub Actions, Azure Pipelines

#### Development

Developer-friendly with helpful warnings.

```bash
docker-compose -f docker-compose.validation.yml run --rm validation --profile development
```

- **Rules**: All rules with warning level
- **Fail On**: Never (warnings only)
- **Use Case**: Learning, exploration, documentation

## Execution Modes

### Containerless Mode (Default, Fastest)

Uses `kantra analyze --run-local` to avoid container overhead.

```bash
# Explicitly set containerless mode
RUN_MODE=local docker-compose -f docker-compose.validation.yml run --rm validation
```

**Pros:**

- Fastest execution (~30% faster than hybrid)
- No Podman/Docker dependency
- Simpler setup

**Cons:**

- Requires analyzer-lsp providers on host (baked into image)
- Less process isolation

**Best For:** Development, CI/CD, fast feedback loops

### Hybrid Mode (Production)

Uses analyzer-lsp containers for isolated analysis.

```bash
# Enable hybrid mode
RUN_MODE=hybrid docker-compose -f docker-compose.validation.yml run --rm validation
```

**Requirements:**

- Host Podman socket mounted: `/run/podman/podman.sock`
- Or Docker socket: `/var/run/docker.sock`

**Pros:**

- Full process isolation
- Production-ready security
- No host analyzer dependencies

**Cons:**

- Slower (~30% overhead)
- Requires container runtime on host
- More complex setup

**Best For:** Production validation, strict isolation requirements

## Volume Mounts

### Workspace (Read-Only)

```yaml
volumes:
  - .:/workspace:ro
```

Source code mounted read-only for security. Validation analyzes but cannot modify files.

### Validation Reports (Persistent)

```yaml
volumes:
  - validation-reports:/workspace/.config/validation/reports
```

Named volume persists across container runs. Contains:

- `static-report/index.html` - Interactive HTML report
- `output.yaml` - Machine-readable results
- `dependencies.yaml` - Dependency graph

**Access Reports:**

```bash
# Inspect volume
docker volume inspect semantic-kernel-validation-reports

# Copy report to host
docker run --rm -v semantic-kernel-validation-reports:/reports -v $(pwd):/host alpine \
  cp -r /reports/static-report /host/

# Or browse in container
docker-compose -f docker-compose.validation.yml run --rm validation bash
# Inside container:
cd .config/validation/reports/static-report
python -m http.server 8000
```

### Test Data (Read-Write)

```yaml
volumes:
  - ./tools/.config/validation/test-data:/workspace/tools/.config/validation/test-data:rw
```

Test fixtures for rule development and testing.

## Label Selectors

Filter rules by label for targeted validation.

### By Category

```bash
# Mandatory rules only
LABEL_SELECTOR="category=mandatory" docker-compose -f docker-compose.validation.yml run --rm validation

# Optional rules only
LABEL_SELECTOR="category=optional" docker-compose -f docker-compose.validation.yml run --rm validation

# Potential issues (warnings)
LABEL_SELECTOR="category=potential" docker-compose -f docker-compose.validation.yml run --rm validation
```

### By Package

```bash
# Metadata rules only
LABEL_SELECTOR="package=metadata" docker-compose -f docker-compose.validation.yml run --rm validation

# Syntax rules only
LABEL_SELECTOR="package=syntax" docker-compose -f docker-compose.validation.yml run --rm validation
```

### Complex Selectors

```bash
# Mandatory metadata rules
LABEL_SELECTOR="category=mandatory,package=metadata" docker-compose -f docker-compose.validation.yml run --rm validation

# High-severity issues
LABEL_SELECTOR="severity in (critical,high)" docker-compose -f docker-compose.validation.yml run --rm validation
```

## Podman Integration

### Enable Podman Socket (Linux)

```bash
# Rootless Podman (recommended)
systemctl --user enable --now podman.socket

# Verify socket
ls -la /run/user/$(id -u)/podman/podman.sock
```

### Update docker-compose.validation.yml

Uncomment Podman socket mount for hybrid mode:

```yaml
volumes:
  # For rootless Podman
  - /run/user/1000/podman/podman.sock:/run/podman/podman.sock:ro

  # For rootful Podman
  # - /run/podman/podman.sock:/run/podman/podman.sock:ro
```

### Windows/macOS

Podman Desktop automatically configures socket. Use containerless mode (`RUN_MODE=local`) for simplicity.

## Security

### Non-Root User

Container runs as `toolsuser:1001` for principle of least privilege.

```dockerfile
RUN groupadd -r toolsuser && useradd -r -g toolsuser -u 1001 -m -s /bin/bash toolsuser
USER toolsuser
```

### Read-Only Workspace

Workspace mounted read-only prevents accidental modifications:

```yaml
volumes:
  - .:/workspace:ro
```

### Capability Restrictions

Minimal capabilities for defense in depth:

```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - CHOWN
  - SETUID
  - SETGID
```

### Resource Limits

Prevent resource exhaustion:

```yaml
deploy:
  resources:
    limits:
      cpus: "1.0"
      memory: 1G
```

## Troubleshooting

### Kantra Not Found

**Error:** `kantra: command not found`

**Solution:** Rebuild container to pull latest Kantra binary:

```bash
docker-compose -f docker-compose.validation.yml build --no-cache
```

### Podman Socket Permission Denied

**Error:** `Error: unable to connect to Podman socket`

**Solution:** Enable Podman socket and verify permissions:

```bash
systemctl --user enable --now podman.socket
chmod 666 /run/user/$(id -u)/podman/podman.sock
```

Or use containerless mode:

```bash
RUN_MODE=local docker-compose -f docker-compose.validation.yml run --rm validation
```

### No Reports Generated

**Error:** No files in `/workspace/.config/validation/reports/`

**Solution:** Check volume mount and permissions:

```bash
# Verify volume exists
docker volume ls | grep validation-reports

# Check container logs
docker-compose -f docker-compose.validation.yml logs validation

# Run with debug output
docker-compose -f docker-compose.validation.yml run --rm validation bash -x /usr/local/bin/validate-yaml
```

### Analysis Fails with Exit Code 1

**Error:** `YAML validation failed with exit code: 1`

**Meaning:** Mandatory rule violations detected. This is expected behavior!

**Action:** Review HTML report to see violations:

```bash
# Copy report to current directory
docker run --rm -v semantic-kernel-validation-reports:/reports -v $(pwd):/host alpine \
  cp -r /reports/static-report ./validation-report

# Open in browser
xdg-open validation-report/index.html  # Linux
open validation-report/index.html      # macOS
start validation-report/index.html     # Windows
```

## Integration Examples

### GitHub Actions

```yaml
name: YAML Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build validation container
        run: docker-compose -f docker-compose.validation.yml build

      - name: Run validation
        run: docker-compose -f docker-compose.validation.yml run --rm validation --profile ci-cd

      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: validation-reports
          path: |
            docker run --rm -v semantic-kernel-validation-reports:/reports -v ${{ github.workspace }}:/host alpine cp -r /reports/static-report /host/
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: yaml-validation
        name: YAML Validation (Mandatory)
        entry: docker-compose -f docker-compose.validation.yml run --rm validation --profile minimal
        language: system
        types: [yaml]
        pass_filenames: false
```

### Makefile Target

```makefile
.PHONY: validate-yaml
validate-yaml:
	docker-compose -f docker-compose.validation.yml run --rm validation

.PHONY: validate-yaml-strict
validate-yaml-strict:
	docker-compose -f docker-compose.validation.yml run --rm validation --profile strict

.PHONY: validate-yaml-report
validate-yaml-report: validate-yaml
	@echo "Opening validation report..."
	docker run --rm -v semantic-kernel-validation-reports:/reports -v $(PWD):/host alpine cp -r /reports/static-report /host/validation-report
	xdg-open validation-report/index.html
```

## Advanced Usage

### Custom Validation Script

Run custom analysis with full control:

```bash
docker-compose -f docker-compose.validation.yml run --rm validation bash -c "
  kantra analyze \
    --input /workspace \
    --output /workspace/.config/validation/reports \
    --rules /workspace/.config/validation/rules \
    --label-selector='severity=critical' \
    --enable-default-rulesets=false \
    --run-local
"
```

### Interactive Debugging

Open shell in validation container:

```bash
docker-compose -f docker-compose.validation.yml run --rm validation bash

# Inside container:
kantra --version
ls -la .config/validation/rules/
bash /usr/local/bin/validate-yaml --profile strict
```

### Export Reports to Host

```bash
# Export all reports
docker run --rm \
  -v semantic-kernel-validation-reports:/reports:ro \
  -v $(pwd)/validation-reports:/export \
  alpine cp -r /reports/. /export/

# Export specific report
docker run --rm \
  -v semantic-kernel-validation-reports:/reports:ro \
  -v $(pwd):/export \
  alpine cp /reports/static-report/index.html /export/validation-report.html
```

## References

- [Kantra CLI Documentation](https://github.com/konveyor/kantra)
- [Red Hat MTA Documentation](https://access.redhat.com/documentation/en-us/migration_toolkit_for_applications/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Podman Rootless Containers](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md)
- [Validation Framework](../tools/.config/validation/README.md)
- [Validation Profiles](../tools/.config/validation/profiles/README.md)
- [Rule Catalog](../.config/copilot/rules-catalog.yml)

## Support

For issues and questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [KANTRA_INTEGRATION_COMPLETE.md](../tools/.config/validation/KANTRA_INTEGRATION_COMPLETE.md)
3. Consult [Validation Framework README](../tools/.config/validation/README.md)
4. Open GitHub issue with container logs and configuration

---

**Version:** 1.0.0
**Updated:** 2025-11-25
**Maintained by:** semantic-kernel-app
