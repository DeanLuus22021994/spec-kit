# YAML Validation Docker - Quick Reference

Fast reference for containerized YAML validation.

## Quick Commands

```bash
# Build validation container
make validate-yaml-docker-build
# OR
docker-compose -f docker-compose.validation.yml build

# Run validation (recommended profile)
make validate-yaml-docker
# OR
docker-compose -f docker-compose.validation.yml run --rm validation

# Run strict validation
make validate-yaml-docker-strict
# OR
docker-compose -f docker-compose.validation.yml run --rm validation --profile strict

# Run mandatory rules only
make validate-yaml-docker-mandatory
# OR
docker-compose -f docker-compose.validation.yml run --rm validation --mandatory

# View reports
make validate-yaml-docker-report
```

## Profiles

| Command                                   | Profile     | Rules      | Fail On          | Time |
| ----------------------------------------- | ----------- | ---------- | ---------------- | ---- |
| `make validate-yaml-docker`               | recommended | Mandatory+ | Mandatory only   | ~12s |
| `make validate-yaml-docker-strict`        | strict      | All 107    | Any violation    | ~19s |
| `make validate-yaml-docker-mandatory`     | minimal     | Mandatory  | Mandatory only   | ~6s  |
| `VALIDATION_PROFILE=ci-cd make ...`       | ci-cd       | Optimized  | CI-blocking      | ~8s  |
| `VALIDATION_PROFILE=development make ...` | development | All        | Never (warnings) | ~12s |

## Environment Variables

```bash
# Set profile
VALIDATION_PROFILE=strict docker-compose -f docker-compose.validation.yml run --rm validation

# Set execution mode
RUN_MODE=hybrid docker-compose -f docker-compose.validation.yml run --rm validation

# Set label selector
LABEL_SELECTOR="category=mandatory" docker-compose -f docker-compose.validation.yml run --rm validation

# Set report format
REPORT_FORMAT="html,yaml,json" docker-compose -f docker-compose.validation.yml run --rm validation
```

## Label Selectors

```bash
# Mandatory rules only
LABEL_SELECTOR="category=mandatory" make validate-yaml-docker

# Specific package
LABEL_SELECTOR="package=metadata" make validate-yaml-docker

# High severity only
LABEL_SELECTOR="severity in (critical,high)" make validate-yaml-docker

# Combined selectors
LABEL_SELECTOR="category=mandatory,package=syntax" make validate-yaml-docker
```

## Execution Modes

### Containerless (Default, Fastest)

```bash
RUN_MODE=local docker-compose -f docker-compose.validation.yml run --rm validation
```

- **Performance:** ~30% faster than hybrid
- **Dependencies:** None (baked into image)
- **Use Case:** Development, CI/CD

### Hybrid (Production)

```bash
RUN_MODE=hybrid docker-compose -f docker-compose.validation.yml run --rm validation
```

- **Requirements:** Podman/Docker socket mounted
- **Security:** Full process isolation
- **Use Case:** Production validation

## Report Access

### Extract Reports to Host

```bash
# Using Makefile (recommended)
make validate-yaml-docker-report

# Manual extraction
docker run --rm \
  -v semantic-kernel-validation-reports:/reports:ro \
  -v $(pwd)/validation-reports:/export \
  alpine cp -r /reports/static-report /export/

# Open in browser
xdg-open validation-reports/static-report/index.html  # Linux
open validation-reports/static-report/index.html      # macOS
start validation-reports/static-report/index.html     # Windows
```

### Browse in Container

```bash
docker-compose -f docker-compose.validation.yml run --rm validation bash
# Inside container:
cd .config/validation/reports/static-report
python -m http.server 8000
# Open http://localhost:8000 in browser
```

## Volume Management

```bash
# List volumes
docker volume ls | grep validation

# Inspect volume
docker volume inspect semantic-kernel-validation-reports

# Remove volume (destructive)
docker volume rm semantic-kernel-validation-reports
```

## Troubleshooting

### Kantra Not Found

```bash
# Rebuild container
docker-compose -f docker-compose.validation.yml build --no-cache
```

### Podman Socket Issues

```bash
# Use containerless mode instead
RUN_MODE=local docker-compose -f docker-compose.validation.yml run --rm validation

# OR enable Podman socket
systemctl --user enable --now podman.socket
```

### No Reports Generated

```bash
# Check volume
docker volume inspect semantic-kernel-validation-reports

# View logs
docker-compose -f docker-compose.validation.yml logs validation

# Debug run
docker-compose -f docker-compose.validation.yml run --rm validation bash -x /usr/local/bin/validate-yaml
```

### Out of Memory

Edit `docker-compose.validation.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G # Increase from 1G
```

## Integration Examples

### GitHub Actions

```yaml
- name: YAML Validation
  run: make validate-yaml-docker-build && make validate-yaml-docker

- name: Upload Reports
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: validation-reports
    path: validation-reports/
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: yaml-validation
        name: YAML Validation
        entry: make validate-yaml-docker-mandatory
        language: system
        types: [yaml]
        pass_filenames: false
```

### VS Code Task

```json
{
  "label": "YAML Validation (Docker)",
  "type": "shell",
  "command": "make validate-yaml-docker",
  "problemMatcher": []
}
```

## Files Reference

| File                                                      | Purpose                      |
| --------------------------------------------------------- | ---------------------------- |
| `dockerfiles/validation.Dockerfile`                       | Container definition         |
| `docker-compose.validation.yml`                           | Service configuration        |
| `dockerfiles/validation.README.md`                        | Comprehensive documentation  |
| `Makefile`                                                | Validation targets           |
| `tools/docker-compose.tools.yml`                          | Integrated tools+validation  |
| `tools/.config/scripts/validate-yaml.sh`                  | Validation automation script |
| `tools/.config/validation/DOCKER_INTEGRATION_COMPLETE.md` | Implementation summary       |

## Performance Tips

1. **Use containerless mode for speed:**

   ```bash
   RUN_MODE=local make validate-yaml-docker
   ```

2. **Use minimal profile for pre-commit:**

   ```bash
   VALIDATION_PROFILE=minimal make validate-yaml-docker
   ```

3. **Cache Docker layers:**

   ```bash
   # Don't use --no-cache unless necessary
   docker-compose -f docker-compose.validation.yml build
   ```

4. **Use label selectors for targeted checks:**
   ```bash
   LABEL_SELECTOR="category=mandatory,package=metadata" make validate-yaml-docker
   ```

## Common Workflows

### Daily Development

```bash
make validate-yaml-docker
```

### Pre-commit Check

```bash
make validate-yaml-docker-mandatory
```

### Pre-release Validation

```bash
make validate-yaml-docker-strict
make validate-yaml-docker-report
```

### CI/CD Pipeline

```bash
VALIDATION_PROFILE=ci-cd make validate-yaml-docker
```

### Debug Rule Issues

```bash
docker-compose -f docker-compose.validation.yml run --rm validation bash
# Inside container:
kantra analyze --input /workspace --rules /workspace/.config/validation/rules --run-local -v
```

## Support

- **Full Documentation:** [validation.README.md](./validation.README.md)
- **Implementation Details:** [DOCKER_INTEGRATION_COMPLETE.md](../tools/.config/validation/DOCKER_INTEGRATION_COMPLETE.md)
- **Validation Framework:** [tools/.config/validation/README.md](../tools/.config/validation/README.md)
- **Kantra CLI:** https://github.com/konveyor/kantra

---

**Version:** 1.0.0
**Updated:** 2025-11-25
