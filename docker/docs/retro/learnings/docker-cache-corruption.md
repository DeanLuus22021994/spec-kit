# Learning: Docker Cache Can Hide Layer Corruption

**Date:** November 24, 2025
**Context:** Embeddings Service Restart Loop
**Severity:** 🔴 CRITICAL - Service Down

---

## The Symptom

```python
SyntaxError: unexpected character after line continuation character
```

Python file appeared to have literal `\n` instead of actual newlines.

---

## The Investigation

**Local file check:**

```bash
cat semantic/embeddings/main.py
# Result: VALID Python syntax, proper newlines
```

**False alarm?** No—Docker image had corrupted layer.

---

## Root Cause

Previous `docker-compose build` cached a corrupted layer:

- COPY operation may have introduced escape sequences
- Cache stored the bad layer
- Every rebuild reused the corrupt cache
- Local file was correct; Docker image was not

---

## The Fix

```bash
docker-compose build --no-cache embeddings
docker-compose up -d embeddings
```

**Result:** Service started successfully. Logs showed:

```
INFO: Uvicorn running on http://0.0.0.0:8001
```

---

## What We Learned

### Cache is Fast But Not Always Safe

**Build Cache Benefits:**

- ✅ Faster builds (reuse unchanged layers)
- ✅ Bandwidth savings (skip re-downloads)

**Build Cache Risks:**

- ❌ Corruption persists across builds
- ❌ File changes may not propagate
- ❌ Hard to diagnose (local file differs from image)

### When to Use `--no-cache`

**Always use when:**

- Syntax errors don't match local files
- Mysterious failures after file edits
- File corruption suspected
- Debugging weird behavior

**Performance hit acceptable** when fixing critical bugs.

---

## Detection Pattern

```
1. Error in container logs
2. Check local file → File is correct
3. Rebuild image → Error persists
4. Conclusion: Cached layer is corrupt
5. Solution: --no-cache rebuild
```

---

## Prevention Strategy

**Multi-stage builds with explicit cache control:**

```dockerfile
# Force cache invalidation for critical layers
COPY --chown=appuser:appuser semantic/embeddings/main.py /app/main.py
RUN sha256sum /app/main.py > /tmp/checksum.txt
```

**Or:** Regularly clean build cache (`docker builder prune`)

---

## Applied Knowledge

- **Cache is an optimization, not a guarantee**
- **Logs are truth, cache can lie**
- **When in doubt, nuke the cache**
