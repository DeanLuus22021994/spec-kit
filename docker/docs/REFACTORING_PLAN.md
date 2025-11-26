# Comprehensive Codebase Refactoring Plan

**Date:** November 25, 2025
**Branch:** tools-enhancement
**Analyst:** GitHub Copilot
**GPU:** RTX 3050 6GB, CUDA 13.0, Driver 581.57
**Docker:** v28.5.2, WSL2 backend, 10GB memory

---

## Executive Summary

This document provides a comprehensive analysis of the semantic-kernel-app codebase for refactoring opportunities. The analysis covers YAML configuration architecture, obsolete files, GPU acceleration gaps, agent tracing requirements, subagent optimization patterns, and volume audit findings.

---

## 1. YAML Config Architecture Analysis

### 1.1 Existing Config Files in `.config/`

| File                       | Purpose                 | Services/Features Controlled      | Real-Time Toggle Support      |
| -------------------------- | ----------------------- | --------------------------------- | ----------------------------- |
| `cli.yml`                  | CLI command definitions | sk-cli commands, API endpoints    | ❌ No                         |
| `dotnet-dependencies.yml`  | .NET package versions   | NuGet packages, auto-provisioning | ❌ No                         |
| `dotnet-tools.json`        | .NET local tools        | dotnet-ef, formatting tools       | ❌ No                         |
| `environment.yml`          | Environment variables   | All services env vars             | ⚠️ Partial (via env)          |
| `github-workflows.yml`     | CI/CD configuration     | GitHub Actions workflows          | ❌ No                         |
| `gpu-resources.yml`        | GPU/CUDA settings       | VRAM partitioning, scheduling     | ✅ Yes (toggles section)      |
| `host-analysis-report.yml` | System baseline         | Host resource monitoring          | ❌ No (diagnostic)            |
| `infrastructure.yml`       | Network/security config | Docker networks, logging          | ❌ No                         |
| `optimization-toggles.yml` | Runtime optimizations   | GPU, caching, performance         | ✅ Yes (comprehensive)        |
| `ports.yml`                | Port allocations        | All service ports                 | ❌ No                         |
| `pr-validation.yml`        | PR checks               | Build, test, lint jobs            | ❌ No                         |
| `python-dependencies.yml`  | Python packages         | pip packages, versions            | ❌ No                         |
| `semantic-kernel.yml`      | SK engine config        | Kernels, plugins, memory          | ⚠️ Partial (filters)          |
| `services.yml`             | Service definitions     | All Docker services, tiers        | ✅ Yes (optimization_toggles) |
| `versions.yml`             | Version matrix          | All technology versions           | ❌ No                         |

### 1.2 Copilot Context Files (`.config/copilot/`)

| Category    | Files   | Purpose                                                           |
| ----------- | ------- | ----------------------------------------------------------------- |
| workflows/  | 8 files | Operational procedures (github-cli, docker, deferred-items, etc.) |
| patterns/   | 2 files | Documentation, version-control patterns                           |
| standards/  | 4 files | Code quality, architecture, infrastructure, CI/CD                 |
| references/ | 6 files | Service catalog, technology stack, troubleshooting                |

### 1.3 Real-Time Toggle Capability Assessment

**✅ Fully Supported (Hot-Reload):**

- `GPU_ENABLED` - Master GPU toggle
- `CUDA_MIXED_PRECISION` - FP16 optimization
- `ENABLE_FLASH_ATTENTION` - Memory-efficient attention
- `CUDA_TF32_ENABLED` - TensorFloat-32 matmul
- `ENABLE_DYNAMIC_BATCHING` - Adaptive batch sizes
- `CUDA_AGGRESSIVE_GC` - Memory cleanup
- `ENABLE_EMBEDDING_CACHE` - Redis embedding cache
- `ENABLE_COMPLETION_CACHE` - Completion cache
- `ENABLE_MEMORY_CACHE` - In-memory cache

**⚠️ Requires Container Restart:**

- `CUDA_MEMORY_POOL` - Memory pooling
- `CUDA_EXPANDABLE_SEGMENTS` - PyTorch allocator
- `GPU_TIME_SLICED` - GPU sharing mode
- `ENABLE_CONNECTION_POOLING` - DB/cache pools
- WSL2 memory/processor limits

### 1.4 Missing for Full YAML-Driven Architecture

| Gap                       | Description                                      | Priority |
| ------------------------- | ------------------------------------------------ | -------- |
| **Service Discovery**     | No dynamic service registration/discovery config | Medium   |
| **Feature Flags**         | No centralized feature flag system               | High     |
| **Secret Management**     | Secrets hardcoded in compose, not in config      | High     |
| **Log Levels**            | No runtime log level toggle per service          | Medium   |
| **Rate Limiting**         | Defined in YAML but not wired to services        | Medium   |
| **Circuit Breaker**       | Config exists but no implementation              | Medium   |
| **Health Check Tuning**   | Intervals/timeouts not configurable at runtime   | Low      |
| **Tracing/Observability** | No OpenTelemetry/Jaeger configuration            | High     |

---

## 2. Files to Archive

### 2.1 Duplicate/Redundant Validation Rules

| File                                            | Reason                                                                      | Archive To                 |
| ----------------------------------------------- | --------------------------------------------------------------------------- | -------------------------- |
| `custom-rules/anchor-pattern-validation.yaml`   | Duplicated in `tools/.config/validation/rules/metadata/anchors.yaml`        | `docs/archive/validation/` |
| `custom-rules/file-organization-validation.yml` | Duplicated in `tools/.config/validation/rules/structure/`                   | `docs/archive/validation/` |
| `custom-rules/indentation-validation.yaml`      | Duplicated in `tools/.config/validation/rules/syntax/indentation.yaml`      | `docs/archive/validation/` |
| `custom-rules/metadata-validation.yaml`         | Duplicated in `tools/.config/validation/rules/metadata/metadata-block.yaml` | `docs/archive/validation/` |
| `custom-rules/quoting-validation.yaml`          | Duplicated in `tools/.config/validation/rules/syntax/quoting.yaml`          | `docs/archive/validation/` |
| `custom-rules/ruleset.yaml`                     | Superseded by `tools/.config/validation/rules/ruleset.yaml`                 | `docs/archive/validation/` |

### 2.2 Test/Generated Files

| File                                      | Reason                                                  | Archive To                   |
| ----------------------------------------- | ------------------------------------------------------- | ---------------------------- |
| `.devcontainer/merged-compose-test.yml`   | Generated test file with exposed secrets (RUNNER_TOKEN) | DELETE (security risk)       |
| `.devcontainer/docker-compose.subnet.yml` | Development experiment, not production                  | `docs/archive/devcontainer/` |

### 2.3 Legacy Documentation References

| File                                                                   | Reason                     | Action                               |
| ---------------------------------------------------------------------- | -------------------------- | ------------------------------------ |
| `tools/.config/validation/rules/ruleset.yaml` → `legacy_rules` section | Documents deprecated files | Keep as-is (provides migration path) |

### 2.4 Recommended Archive Structure

```
docs/archive/
├── validation/           # Deprecated validation rules
│   ├── custom-rules/     # Move entire custom-rules/ folder
│   └── README.md         # Explain why archived
├── devcontainer/         # Development experiments
│   └── docker-compose.subnet.yml
└── README.md             # Archive index
```

---

## 3. GPU Acceleration Gaps

### 3.1 Current GPU Utilization

| Service    | GPU Enabled | Dockerfile Config        | docker-compose.yml Config |
| ---------- | ----------- | ------------------------ | ------------------------- |
| embeddings | ✅          | ❌ Alpine base (no CUDA) | ✅ runtime: nvidia        |
| engine     | ✅          | ❌ Alpine base (no CUDA) | ✅ runtime: nvidia        |
| vector     | ✅          | ❌ Base qdrant image     | ✅ runtime: nvidia        |

### 3.2 Critical Gap: Dockerfiles Missing CUDA Support

**Problem:** All GPU services use Alpine or standard base images without NVIDIA CUDA support, but docker-compose.yml configures `runtime: nvidia`.

**Current State:**

```dockerfile
# embeddings.Dockerfile
FROM python:3.14-alpine AS base  # ❌ No CUDA

# engine.Dockerfile
FROM mcr.microsoft.com/dotnet/aspnet:10.0-alpine AS runtime  # ❌ No CUDA

# vector.Dockerfile
FROM qdrant/qdrant:v1.7.4-unprivileged  # ❌ No GPU acceleration
```

**Required Changes:**

| Service    | Current Base                 | Required Base                                | Purpose               |
| ---------- | ---------------------------- | -------------------------------------------- | --------------------- |
| embeddings | `python:3.14-alpine`         | `nvidia/cuda:13.0-cudnn-runtime-ubuntu24.04` | PyTorch GPU inference |
| engine     | `dotnet/aspnet:10.0-alpine`  | `mcr.microsoft.com/dotnet/aspnet:10.0-jammy` | .NET GPU interop      |
| vector     | `qdrant:v1.7.4-unprivileged` | `qdrant/qdrant:v1.7.4` (with GPU build)      | HNSW GPU indexing     |

### 3.3 Missing GPU Optimizations

| Optimization      | Config Exists               | Implemented                |
| ----------------- | --------------------------- | -------------------------- |
| CUDA 13.0 Toolkit | ✅ versions.yml             | ❌ Not in Dockerfiles      |
| PyTorch CUDA 13.0 | ✅ versions.yml             | ❌ Not installed           |
| cuDNN 9.1.2       | ✅ versions.yml             | ❌ Not in base images      |
| Flash Attention   | ✅ optimization-toggles.yml | ❌ No flash-attn package   |
| Triton compiler   | ✅ versions.yml             | ❌ Not installed           |
| Mixed Precision   | ✅ optimization-toggles.yml | ❌ No torch.cuda.amp usage |

### 3.4 VRAM Budget (RTX 3050 6GB)

Current allocation in `gpu-resources.yml`:

```
embeddings: 3072 MB (50%)
engine:     1536 MB (25%)
vector:      512 MB (8%)
system:      512 MB (reserved)
───────────────────────────
Total:      5632 MB (92% of 6144 MB)
```

**Issue:** Services aren't actually using GPU - config is correct but implementation is missing.

---

## 4. Agent Tracing Implementation Plan

### 4.1 Current State

- OpenTelemetry packages referenced in `dotnet-dependencies.yml`:
  - `OpenTelemetry.Exporter.Console: 1.9.0`
  - `OpenTelemetry.Extensions.Hosting: 1.9.0`
- Monitoring ports reserved in `ports.yml`: `9000-9999`
- No Jaeger/Zipkin service defined
- No tracing configuration in Semantic Kernel engine

### 4.2 Required Infrastructure

```yaml
# Add to docker-compose.yml
services:
  jaeger:
    image: jaegertracing/all-in-one:1.53
    container_name: semantic-kernel-jaeger
    ports:
      - "16686:16686" # UI
      - "4317:4317" # OTLP gRPC
      - "4318:4318" # OTLP HTTP
      - "6831:6831/udp" # Jaeger thrift
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - backend-network
    volumes:
      - jaeger-data:/badger
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
```

### 4.3 Configuration Files to Add

| File                                          | Purpose                        |
| --------------------------------------------- | ------------------------------ |
| `.config/tracing.yml`                         | OpenTelemetry configuration    |
| `.config/copilot/workflows/agent-tracing.yml` | Tracing workflow documentation |

### 4.4 Tracing Config Schema

```yaml
# .config/tracing.yml
tracing:
  enabled: true
  exporter:
    type: "otlp"
    endpoint: "http://jaeger:4317"
    protocol: "grpc"

  sampling:
    type: "probabilistic"
    probability: 1.0 # 100% in dev

  instrumentation:
    semantic_kernel:
      trace_prompts: true
      trace_completions: true
      trace_memory_operations: true
    http:
      capture_headers: true
    database:
      capture_queries: true

  service_names:
    engine: "semantic-kernel-engine"
    embeddings: "semantic-kernel-embeddings"
    backend: "semantic-kernel-backend"
```

### 4.5 Implementation Steps

1. **Add Jaeger service** to docker-compose.yml
2. **Create .config/tracing.yml** configuration
3. **Add NuGet packages** to engine/backend:
   - `OpenTelemetry.Instrumentation.AspNetCore`
   - `OpenTelemetry.Exporter.OpenTelemetryProtocol`
   - `OpenTelemetry.Instrumentation.Http`
4. **Wire up in Program.cs** for each service
5. **Add Semantic Kernel activity sources** for AI operation tracing
6. **Update .config/ports.yml** with Jaeger ports

---

## 5. Subagent Optimization Patterns

Based on `docs/retro/workforce/subagent-capabilities.md`:

### 5.1 Ideal Subagent Tasks for This Codebase

| Task Category            | Examples                                                  | Parallelizable |
| ------------------------ | --------------------------------------------------------- | -------------- |
| **Batch Validation**     | "Validate all YAML files in .config/"                     | ✅ Yes         |
| **File Pattern Updates** | "Update version numbers across all csproj files"          | ✅ Yes         |
| **Pre-flight Checks**    | "Verify Docker health, Git status, configs before deploy" | ✅ Yes         |
| **Report Generation**    | "Generate Pylint report for tools/"                       | ✅ Yes         |
| **Codebase Search**      | "Find all usages of IKernel interface"                    | ✅ Yes         |
| **Documentation Audit**  | "Check all README files for outdated info"                | ✅ Yes         |
| **Dependency Analysis**  | "List all NuGet packages across projects"                 | ✅ Yes         |

### 5.2 Tasks NOT Suitable for Subagents

| Task Type                    | Reason                                  |
| ---------------------------- | --------------------------------------- |
| **Iterative Debugging**      | Requires hypothesis state across cycles |
| **Architecture Decisions**   | Needs conversation context              |
| **User Preference Tasks**    | "Should I use approach A or B?"         |
| **Incremental Code Changes** | Needs understanding of prior decisions  |
| **Multi-step Refactoring**   | State loss between invocations          |

### 5.3 Recommended Subagent Task Templates

```yaml
# Suggested .config/copilot/workflows/subagent-tasks.yml
subagent_tasks:
  pre_commit_validation:
    description: "Run before every commit"
    parallel_calls:
      - "Validate all YAML configs"
      - "Check for duplicate anchor names"
      - "Verify Dockerfile base images"
      - "Run Pylint on Python files"
    context_required: false

  docker_health_check:
    description: "Pre-deployment validation"
    parallel_calls:
      - "Check all services healthy"
      - "Verify volume mounts"
      - "Validate GPU availability"
      - "Check port conflicts"
    context_required: false

  codebase_inventory:
    description: "Generate project overview"
    parallel_calls:
      - "Count files by extension"
      - "List all service definitions"
      - "Extract version numbers"
      - "Map service dependencies"
    context_required: false
```

---

## 6. Volume Audit Results

### 6.1 Main docker-compose.yml - ✅ COMPLIANT

All volumes are properly defined as named volumes:

```yaml
volumes:
  # ✅ All using named volumes, no host mounts
  registry-data:
  registry-logs:
  postgres_data:
  vector_data:
  embeddings-cache:
  engine-plugins:
  # ... (40+ named volumes total)
```

### 6.2 Host Mount Violations Found

| File                                        | Line     | Mount                                                   | Severity                   |
| ------------------------------------------- | -------- | ------------------------------------------------------- | -------------------------- |
| `tools/docker-compose.tools.yml`            | 33       | `- ..:/app:ro`                                          | ⚠️ Medium                  |
| `tools/docker-compose.tools.yml`            | 43       | `- ./.config/validation/test-data:/app/...`             | ⚠️ Medium                  |
| `tools/docker-compose.tools.yml`            | 69       | `- ..:/workspace:ro`                                    | ⚠️ Medium                  |
| `tools/docker-compose.tools.yml`            | 78       | `- ./.config/validation/test-data:/workspace/...`       | ⚠️ Medium                  |
| `docker-compose.validation.yml`             | 47       | `- ./tools/.config/validation/test-data:/workspace/...` | ⚠️ Medium                  |
| `.devcontainer/docker-compose.override.yml` | 24       | `- ..:/workspace:cached`                                | ⚠️ Expected (devcontainer) |
| `.devcontainer/docker-compose.override.yml` | 34       | `- ../src/backend:/src/backend:cached`                  | ⚠️ Expected (devcontainer) |
| `.devcontainer/docker-compose.override.yml` | 52       | `- ../src/engine:/src/engine:cached`                    | ⚠️ Expected (devcontainer) |
| `.devcontainer/merged-compose-test.yml`     | Multiple | Bind mounts throughout                                  | 🔴 HIGH (generated file)   |

### 6.3 Remediation Plan

**For tools/docker-compose.tools.yml:**

```yaml
# Replace host mounts with named volumes + initialization
volumes:
  tools-workspace:
    driver: local
  tools-validation-test-data:
    driver: local
# Use docker cp or init container to populate
```

**For docker-compose.validation.yml:**

```yaml
# Same approach - named volumes with initialization
volumes:
  validation-workspace:
    driver: local
```

**For .devcontainer/:**

- Host mounts are **expected and acceptable** for devcontainer hot-reload
- Document this exception in README

**For merged-compose-test.yml:**

- **DELETE immediately** - contains exposed RUNNER_TOKEN secret
- Add to `.gitignore` if regenerated

---

## 7. Summary of Actions

### High Priority

1. ❌ **DELETE** `.devcontainer/merged-compose-test.yml` (security risk - exposed token)
2. 🔧 **Fix** Dockerfiles to use CUDA-enabled base images
3. 📁 **Create** `docs/archive/` directory structure
4. 📁 **Move** `custom-rules/` to `docs/archive/validation/`
5. ➕ **Add** Jaeger service for agent tracing
6. ➕ **Create** `.config/tracing.yml`

### Medium Priority

7. 🔧 **Convert** host mounts in `tools/docker-compose.tools.yml` to named volumes
8. 🔧 **Convert** host mounts in `docker-compose.validation.yml` to named volumes
9. ➕ **Add** feature flag system configuration
10. ➕ **Create** `.config/copilot/workflows/subagent-tasks.yml`
11. 🔧 **Implement** rate limiting from config
12. 🔧 **Wire up** circuit breaker config

### Low Priority

13. 📝 **Document** devcontainer host mount exceptions
14. ➕ **Add** log level runtime toggles
15. ➕ **Add** health check tuning toggles
16. 🔧 **Clean up** legacy_rules references after verification

---

## 8. File Changes Summary

| Action      | Count | Files                                                               |
| ----------- | ----- | ------------------------------------------------------------------- |
| DELETE      | 1     | merged-compose-test.yml                                             |
| ARCHIVE     | 7     | custom-rules/\*                                                     |
| CREATE      | 4     | tracing.yml, archive structure, subagent-tasks.yml, archive READMEs |
| MODIFY      | 5     | 3 Dockerfiles, 2 docker-compose files                               |
| ADD SERVICE | 1     | Jaeger in docker-compose.yml                                        |

---

_Report generated by GitHub Copilot analysis on November 25, 2025_
