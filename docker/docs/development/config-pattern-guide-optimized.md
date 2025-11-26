# .config/ Pattern Guide

**Updated:** 2025-11-24 | **Status:** Active | **Adoption:** 56% (5/9 dirs)

## Overview

Standardized structure for config, build artifacts, and tooling. Promotes discoverability, maintainability, AI intelligence, and cleanliness.

## Structure

```
<directory>/
├── .config/
│   ├── copilot/              # AI context (REQUIRED: index.yml 50+ lines)
│   ├── docker/               # Containers (Dockerfile + .dockerignore)
│   └── scripts/              # Automation
├── .gitignore                # Pollution prevention (REQUIRED)
└── [source files]
```

**Deprecated:** `.config/documentation/` (commit 030910d). Use centralized `docs/` root.

## Core Principles

| Principle              | Implementation                                        | Benefit                    |
| ---------------------- | ----------------------------------------------------- | -------------------------- |
| **Baked Dependencies** | `RUN pip install` in Dockerfile                       | Zero latency, reproducible |
| **Non-root Users**     | `USER 1001` in containers                             | Security, consistency      |
| **Cache Prevention**   | `.gitignore` excludes `__pycache__/`, `node_modules/` | Clean git, no artifacts    |
| **Copilot Context**    | YAML in `.config/copilot/index.yml`                   | Accurate AI suggestions    |
| **Build Optimization** | `.dockerignore` excludes cache                        | ~90% size reduction        |

## Adoption Roadmap

| Phase         | Status | Directories                                      | Achievement              |
| ------------- | ------ | ------------------------------------------------ | ------------------------ |
| 1: Foundation | ✅     | `tests/`, `tools/`                               | Core pattern established |
| 2: Extensions | ✅     | `src/frontend/`, `semantic/{embeddings,vector}/` | 56% adoption             |
| 3: Backend    | ⏳     | `src/{backend,business,engine,gateway}/`         | Target: 100%             |

## Implementation Checklist

### Required

- [ ] Create `.config/copilot/index.yml` (50+ lines: description, architecture, technologies, workflows)
- [ ] Create `.gitignore` (exclude cache: `__pycache__/`, `node_modules/`, `bin/`, `obj/`)
- [ ] Move existing configs to `.config/` (update all code references)

### Optional

- [ ] Add `.config/docker/` (Dockerfile with baked deps, non-root user UID 1001)
- [ ] Add `.config/scripts/` (automation, document in copilot/scripts.yml)

### Validation

- [ ] Run `make validate-pattern` (local runner)
- [ ] Test builds/tests unchanged
- [ ] Commit: `refactor: organize <dir> with .config/ pattern`

## Examples

<details>
<summary>Frontend (React/TypeScript)</summary>

```
src/frontend/
├── .config/
│   ├── copilot/index.yml
│   ├── .eslintrc.json
│   ├── .prettierrc
│   └── tsconfig.json
├── .gitignore          # node_modules/, dist/
└── src/
```

</details>

<details>
<summary>Python Service</summary>

```
semantic/embeddings/
├── .config/
│   ├── copilot/index.yml
│   └── config.yml
├── .gitignore          # __pycache__/
└── main.py
```

</details>

<details>
<summary>.NET Service</summary>

```
src/backend/
├── .config/
│   ├── copilot/index.yml
│   └── appsettings.json
├── .gitignore          # bin/, obj/
└── backend.csproj
```

</details>

## Anti-patterns

| ❌ Problem                            | ✅ Solution                  |
| ------------------------------------- | ---------------------------- |
| `CMD pip install -r requirements.txt` | Bake in `RUN` layer          |
| Configs at root (scattered)           | Move to `.config/`           |
| Missing `.gitignore`                  | Create with cache exclusions |
| `USER root` in Dockerfile             | Use `USER 1001`              |
| `.config/documentation/`              | Use centralized `docs/`      |

## Validation

### Manual

```bash
find . -type d -name ".config" | wc -l           # Adoption count
find . -path "*/.config/copilot/index.yml" | wc -l  # Context files
```

### Automated

```bash
make validate-pattern  # Local runner (not GitHub Actions)
```

**Checks:** Copilot context (50+ lines), no cache pollution, non-root users, baked deps, adoption %

## Migration

1. **Audit:** `ls -la` (find scattered configs)
2. **Create:** `mkdir -p .config/{copilot,docker,scripts}`
3. **Index:** Create `.config/copilot/index.yml` (50+ lines)
4. **Move:** `mv appsettings.json .config/`
5. **Update:** Search/replace old paths in code
6. **Ignore:** Add cache patterns to `.gitignore`
7. **Test:** Build + test unchanged
8. **Commit:** `refactor: organize <dir> with .config/ pattern`

## Pattern Evolution

**Tracked in:**

- This document: `docs/development/config-pattern-guide.md`
- Contributing: `CONTRIBUTING.md`
- Validation: `tools/.config/scripts/validate-pattern.sh` + `make validate-pattern`

**History:**

1. Phase 1 (d083555, 530035b): Established in tools/, tests/
2. Phase 2 (54dc918, 314981b): Extended to frontend, semantic services
3. Phase 3 (030910d): Centralized docs, deprecated `.config/documentation/`
4. Phase 4 (7ea5dcd, b5962be): Consolidated documentation, added enforcement

## Consistency Validation

**Last Validated:** 2025-11-24 | **Status:** ✅ 100% (where applied)

### Metrics

| Metric              | Score | Details                      |
| ------------------- | ----- | ---------------------------- |
| Directory Structure | 100%  | Identical `.config/` pattern |
| Baked Dependencies  | 100%  | Pre-installed in Dockerfile  |
| Non-root Users      | 100%  | UID 1001                     |
| Cache Prevention    | 100%  | `.gitignore` files present   |
| Copilot Context     | 100%  | `copilot/` subdirectory      |
| Build Optimization  | 100%  | `.dockerignore` files        |

### Adoption Progress

| Directory                      | Status | Commit  | Notes                      |
| ------------------------------ | ------ | ------- | -------------------------- |
| `tests/.config/`               | ✅     | 530035b | 5 context files, 4 subdirs |
| `tools/.config/`               | ✅     | d083555 | 3 context files, 4 subdirs |
| `src/frontend/.config/`        | ✅     | 54dc918 | 1 context, 4 config files  |
| `semantic/embeddings/.config/` | ✅     | 314981b | 1 context, config.yml      |
| `semantic/vector/.config/`     | ✅     | 314981b | 1 context, config.yml      |
| `src/backend/`                 | ⏳     | -       | Pending (appsettings.json) |
| `src/business/`                | ⏳     | -       | Pending (minimal config)   |
| `src/engine/`                  | ⏳     | -       | Pending (kernel configs)   |
| `src/gateway/`                 | ⏳     | -       | Pending (nginx configs)    |

### Benefits Achieved

| Before              | After                              |
| ------------------- | ---------------------------------- |
| Scattered configs   | Organized `.config/`               |
| Mixed concerns      | Separated code/config              |
| No AI context       | Rich YAML context                  |
| Cache pollution     | `.gitignore` prevention            |
| Full Docker context | ~90% reduction via `.dockerignore` |

## References

- **Baked Dependencies:** `tests/.config/documentation/BAKED_DEPENDENCIES.md`
- **Copilot Examples:** `{tests,tools,src/frontend}/.config/copilot/index.yml`
- **Documentation:** `docs/` (MkDocs site)
- **Validation:** `tools/.config/scripts/validate-pattern.sh`
- **Standards:** `.github/DOCUMENTATION_STANDARDS.md`

---

**Status:** Living document | **Location:** `docs/development/config-pattern-guide.md`
