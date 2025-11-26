# Learning: MkDocs Has Strict Directory Requirements

**Date:** November 24, 2025
**Context:** DevSite Service Failing to Start
**Severity:** 🟡 MODERATE - Documentation Inaccessible

---

## The Errors (3-Part Failure)

```
Error 1: Config file 'mkdocs.yml' does not exist
Error 2: Config value 'docs_dir': The path '/docs/docs' isn't an existing directory
Error 3: The "awesome-pages" plugin is not installed
```

---

## Root Cause Analysis

### Issue 1: Directory Structure Mismatch

**What we had:**

```
/docs/
  index.md
  other.md
  mkdocs.yml
```

**What MkDocs expects:**

```
/docs/
  mkdocs.yml          <- Config at root
  docs/               <- Content in subdirectory
    index.md
    other.md
```

**MkDocs is STRICT:** Content MUST be in `docs/` subdirectory unless explicitly overridden.

---

### Issue 2: Invalid docs_dir Override

```yaml
# In mkdocs.yml - THIS FAILS:
docs_dir: .
```

**Why it fails:** MkDocs doesn't allow docs_dir to be parent of config file.

**The rule:** `docs_dir` cannot be `.` when mkdocs.yml is in same directory.

---

### Issue 3: Plugin Assumptions

```yaml
plugins:
  - search
  - minify # ❌ Not in squidfunk/mkdocs-material
  - awesome-pages # ❌ Not in base image
  - git-committers # ❌ Requires installation
```

**Base image only includes:** `search` plugin (built-in to material theme)

---

## The Fix

**Phase 1 - Directory Structure:**

```dockerfile
RUN mkdir -p /docs/site /docs/.cache /docs/docs
COPY ./docs/*.md /docs/docs/
COPY ./docs/*/ /docs/docs/
COPY ./docs/mkdocs.yml /docs/mkdocs.yml
WORKDIR /docs
```

**Phase 2 - Remove docs_dir:**

```yaml
# REMOVED: docs_dir: .
# Let MkDocs use default: docs/
```

**Phase 3 - Minimal Plugins:**

```yaml
plugins:
  - search # Only built-in plugin
```

---

## What We Learned

### MkDocs Directory Rules (Non-Negotiable)

1. **Config location:** Root of docs workspace
2. **Content location:** `docs/` subdirectory (default name)
3. **Cannot override:** docs_dir to parent directory
4. **Output location:** `site/` (generated)

### Plugin Management

- **Base image != all plugins**
- Only use plugins available in Docker image
- Or: Install plugins explicitly in Dockerfile
- Keep it minimal: `search` is often enough

---

## Pattern Recognition

```
MkDocs Error Pattern:
1. "Config file doesn't exist" → Wrong COPY path
2. "docs_dir path doesn't exist" → Directory structure wrong
3. "Plugin not installed" → Remove from config or install
```

---

## Applied Knowledge

- **Don't fight MkDocs conventions** - Follow the structure
- **Minimal plugin config** until you need more
- **Test MkDocs locally** before Dockerizing
- **Directory structure matters** more than you think
