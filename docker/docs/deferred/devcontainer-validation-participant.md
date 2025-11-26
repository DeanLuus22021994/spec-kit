# DevContainer Validation Participant - Deferred Requirement

**Status**: Deferred
**Priority**: Medium
**Created**: 2025-11-24
**Category**: Developer Experience, Infrastructure

## Overview

Implement a validation participant service that can validate DevContainer configurations from the host through a container-exposed port, enabling continuous validation during development without requiring host-installed tools.

## Current State

**Current Implementation**:

- DevContainer validation requires `@devcontainers/cli` installed on host
- Manual validation using `devcontainer read-configuration --workspace-folder .`
- No continuous validation during development
- Configuration errors discovered at container startup time

**Current Limitations**:

1. Host dependency: Requires Node.js and devcontainer CLI on host machine
2. Manual process: Developer must remember to validate before committing
3. No real-time feedback: Errors only discovered during rebuild
4. Limited integration: Cannot validate from within running container

## Proposed Solution

### Architecture

```
┌─────────────────────────────────────────────────────┐
│ Host Machine                                        │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ IDE / Terminal                               │  │
│  │                                              │  │
│  │  HTTP Request → localhost:9090/validate     │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                   │
└─────────────────┼───────────────────────────────────┘
                  │
                  │ Port Forward 9090
                  │
┌─────────────────▼───────────────────────────────────┐
│ DevContainer                                        │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Validation Participant Service               │  │
│  │                                              │  │
│  │ - FastAPI or ASP.NET Core                   │  │
│  │ - Exposes /validate endpoint                │  │
│  │ - Runs devcontainer CLI internally          │  │
│  │ - Returns JSON validation results           │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ DevContainer CLI (@devcontainers/cli)       │  │
│  │ - Installed in container                    │  │
│  │ - Validates devcontainer.json               │  │
│  │ - Validates docker-compose files            │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Service Specification

**Technology**: FastAPI (Python) or ASP.NET Core (C#)

**Endpoints**:

```
POST /validate
  Request Body: {
    "configPath": ".devcontainer/devcontainer.json",
    "workspaceFolder": "/workspace"
  }

  Response: {
    "valid": true|false,
    "errors": [],
    "warnings": [],
    "configuration": { ... },
    "timestamp": "2025-11-24T10:30:00Z"
  }

GET /health
  Response: {
    "status": "healthy",
    "cliVersion": "0.80.1",
    "nodeVersion": "24.11.0"
  }
```

**Port**: 9090 (configurable via environment variable)

### Integration Points

1. **Pre-commit Hook**: Validate before git commit

   ```bash
   curl -X POST http://localhost:9090/validate \
     -H "Content-Type: application/json" \
     -d '{"configPath":".devcontainer/devcontainer.json"}'
   ```

2. **VS Code Task**: Add validation task to `.vscode/tasks.json`

   ```json
   {
     "label": "Validate DevContainer",
     "type": "shell",
     "command": "curl -s http://localhost:9090/validate | jq '.valid'"
   }
   ```

3. **GitHub Actions**: CI validation workflow

   ```yaml
   - name: Validate DevContainer
     run: |
       docker-compose up -d devcontainer
       curl --retry 5 http://localhost:9090/validate
   ```

4. **Watch Mode**: Continuous validation during development
   ```bash
   # Watch for changes and auto-validate
   fswatch .devcontainer/*.json | xargs -n1 -I{} curl http://localhost:9090/validate
   ```

## Benefits

### Developer Experience

- **Real-time Feedback**: Immediate validation results during editing
- **No Host Dependencies**: All tools contained in DevContainer
- **Automated Validation**: Pre-commit hooks prevent invalid configs
- **CI/CD Integration**: Validate in pipeline before deployment

### Reliability

- **Early Error Detection**: Catch configuration errors before rebuild
- **Consistent Environment**: Same validation in dev and CI
- **Version Alignment**: Container CLI version matches container runtime

### Maintainability

- **Centralized Logic**: Single validation service for all scenarios
- **Observable**: Health checks and metrics endpoint
- **Extensible**: Easy to add schema validation, linting, best practices checks

## Implementation Phases

### Phase 1: Basic Validation Service (2-3 hours)

- [ ] Create FastAPI service in `tools/devcontainer-validator/`
- [ ] Install @devcontainers/cli in devcontainer
- [ ] Implement `/validate` endpoint
- [ ] Implement `/health` endpoint
- [ ] Add to docker-compose.override.yml
- [ ] Document API in OpenAPI spec

### Phase 2: Integration (1-2 hours)

- [ ] Add pre-commit hook
- [ ] Create VS Code task
- [ ] Add to RESTART_CHECKLIST.md
- [ ] Update documentation

### Phase 3: Enhanced Validation (3-4 hours)

- [ ] Schema validation for devcontainer.json
- [ ] Docker Compose syntax validation
- [ ] Best practices linting (port conflicts, volume mounts, etc.)
- [ ] Security checks (exposed ports, secrets in env vars)

### Phase 4: CI/CD Integration (1-2 hours)

- [ ] GitHub Actions workflow
- [ ] Add to PR checks
- [ ] Generate validation reports

## Technical Considerations

### Container Startup Order

- Validation service must start before developer needs it
- Add healthcheck to ensure service ready before IDE connects
- Use `depends_on` in docker-compose.override.yml

### Performance

- Cache validation results for 5 seconds (avoid redundant checks)
- Async endpoint to support multiple concurrent validations
- Timeout after 30 seconds for hung validations

### Security

- Bind to localhost only (127.0.0.1:9090)
- No external network access required
- Read-only access to configuration files
- Consider authentication token for production use

### Error Handling

- Graceful degradation if CLI not available
- Clear error messages with remediation steps
- Log validation attempts for debugging

## File Structure

```
tools/
  devcontainer-validator/
    main.py                    # FastAPI service
    requirements.txt           # python dependencies (fastapi, uvicorn)
    Dockerfile                 # Optional: separate service container
    README.md                  # Service documentation
    tests/
      test_validator.py        # Unit tests
      fixtures/
        valid_config.json      # Test fixtures
        invalid_config.json
```

## Configuration

**Environment Variables**:

```bash
VALIDATOR_PORT=9090                    # Service port
VALIDATOR_LOG_LEVEL=INFO              # Logging level
VALIDATOR_CACHE_TTL=5                 # Cache timeout (seconds)
VALIDATOR_CLI_PATH=/usr/local/bin/devcontainer  # CLI path
```

**docker-compose.override.yml**:

```yaml
services:
  devcontainer-validator:
    build:
      context: ../tools/devcontainer-validator
    ports:
      - "${VALIDATOR_PORT:-9090}:9090"
    volumes:
      - ../:/workspace:ro
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9090/health"]
      interval: 10s
      timeout: 5s
      retries: 3
```

## Acceptance Criteria

- [ ] Service starts automatically with devcontainer
- [ ] `/validate` endpoint returns accurate results
- [ ] Invalid configs detected and reported clearly
- [ ] Pre-commit hook prevents invalid config commits
- [ ] Service documented in project README
- [ ] CI workflow validates on PR
- [ ] Response time < 2 seconds for typical configs

## Related Issues

- **Current Fix**: Removed `runArgs` from devcontainer.json (not allowed with dockerComposeFile)
- **Root Cause**: No validation before commit, error discovered at runtime
- **Prevention**: This participant service would catch issue pre-commit

## References

- [DevContainer CLI Documentation](https://github.com/devcontainers/cli)
- [DevContainer Specification](https://containers.dev/implementors/json_reference/)
- [Docker Compose Specification](https://docs.docker.com/compose/compose-file/)
- FastAPI: https://fastapi.tiangolo.com/
- OpenAPI Generator: https://openapi-generator.tech/

## Notes

**Why Not Host Validation?**

- Different Node.js versions on different developer machines
- Manual installation steps (friction for new developers)
- Version drift between host CLI and container runtime
- Cannot validate from within automated container workflows

**Why Port-Based Service?**

- Container-native approach (all tools in container)
- Accessible from host and container
- Easy to integrate with existing tooling (curl, VS Code tasks, git hooks)
- Enables automated testing in CI/CD pipelines
- Can be extended to validate other configs (docker-compose, k8s, etc.)

**Alternative Approaches Considered**:

1. **Shared Volume with Host Watcher**: Complex, requires file system events
2. **SSH into Container**: Overhead, authentication complexity
3. **Docker Exec**: Requires container name, less portable
4. **VS Code Extension**: Platform-specific, harder to use in CI

**Decision**: Port-based HTTP service provides best balance of simplicity, portability, and integration capability.

---

**Next Steps When Implemented**:

1. Move from `docs/deferred/` to `docs/architecture/`
2. Add ADR (Architecture Decision Record) for validation strategy
3. Update CONTRIBUTING.md with validation workflow
4. Add to onboarding documentation
