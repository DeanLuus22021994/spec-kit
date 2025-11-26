# Python Package Updates - Deferred

**Status**: Research Required
**Priority**: Medium
**Created**: 2025-11-24
**Category**: Dependencies, Code Quality
**Impact**: `tools/` directory, `semantic/` directory

## Overview

Major version updates for Python development tools that require breaking change analysis and compatibility testing before implementation.

## Deferred Updates

### isort 5.12.0 → 7.0.0

**Type**: MAJOR - Breaking Changes
**Current Version**: 5.12.0
**Target Version**: 7.0.0
**Status**: ⏳ Research Required

**Reason for Deferral**:
Major version jump with potential breaking changes in import sorting behavior that could affect code organization across the entire Python codebase.

**Impact Areas**:

- All Python files in `semantic/` directory
- All Python files in `tools/` directory
- Pre-commit hook integration
- Compatibility with black 25.11.0

**Required Research**:

- [ ] Review [isort 7.0.0 changelog](https://github.com/PyCQA/isort/releases)
- [ ] Test against codebase to verify no import order changes
- [ ] Check compatibility with black 25.11.0
- [ ] Verify pre-commit hook integration still works
- [ ] Review configuration file changes

**Testing Steps**:

1. Create test branch `feature/isort-7.0.0`
2. Update isort in Dockerfile: `isort==7.0.0`
3. Rebuild tools container
4. Run `isort --check-only --diff semantic/ tools/` to preview changes
5. Apply changes: `isort semantic/ tools/`
6. Verify pylint score remains 10.00/10
7. Test pre-commit hooks with sample commit
8. Review all import changes for correctness

**Acceptance Criteria**:

- [ ] All tests pass
- [ ] Pylint score remains 10.00/10
- [ ] No unexpected import reordering
- [ ] Pre-commit hooks functional
- [ ] Documentation updated

**Estimated Effort**: 1-2 hours

---

### openai 1.12.0 → 2.8.1

**Type**: MAJOR - API Breaking Changes
**Current Version**: 1.12.0
**Target Version**: 2.8.1
**Status**: ⏳ Research Required

**Reason for Deferral**:
Major version with breaking API changes affecting embeddings service. Requires code migration and thorough testing of OpenAI integration.

**Impact Areas**:

- `semantic/embeddings/main.py` - FastAPI embeddings service
- OpenAI client initialization patterns
- Embeddings API endpoints
- Error handling and retry logic
- Response object structures

**Known Breaking Changes**:

- Client initialization pattern changed
- Response object structure modified
- Error classes reorganized
- Streaming API updates
- Authentication method changes

**Required Research**:

- [ ] Review [OpenAI Python SDK 2.x migration guide](https://github.com/openai/openai-python/blob/main/CHANGELOG.md)
- [ ] Check API signature changes for embeddings endpoints
- [ ] Verify async/await patterns still compatible
- [ ] Test error handling changes
- [ ] Review rate limiting and retry logic updates

**Testing Steps**:

1. Create test branch `feature/openai-2.8.1`
2. Update openai in Dockerfile: `openai==2.8.1`
3. Rebuild tools container
4. Update `semantic/embeddings/main.py` per migration guide
5. Test embeddings endpoint: `POST http://localhost:8001/api/embeddings`
6. Test batch embeddings endpoint: `POST http://localhost:8001/api/embeddings/batch`
7. Verify health check: `GET http://localhost:8001/health`
8. Run pylint validation
9. Test integration with Semantic Kernel engine
10. Load test to verify rate limiting

**Acceptance Criteria**:

- [ ] All API endpoints functional
- [ ] Error handling works correctly
- [ ] Integration tests pass
- [ ] Performance unchanged or improved
- [ ] Documentation updated with new patterns

**Estimated Effort**: 3-4 hours

---

## Update Strategy

### Current Approach

Dependencies are baked directly into `tools/.config/docker/Dockerfile` for zero-latency execution. Updates require:

1. Modify version in Dockerfile `RUN pip install` section
2. Rebuild container: `docker build -t semantic-kernel-tools:latest -f tools/.config/docker/Dockerfile tools/`
3. Test container: `docker run --rm semantic-kernel-tools:latest python -c "import <package>"`
4. Verify functionality with actual workload

### Pre-Update Checklist

- [ ] Create feature branch for update
- [ ] Review changelog for breaking changes
- [ ] Update Dockerfile with new version
- [ ] Rebuild container
- [ ] Run test suite
- [ ] Verify code quality (pylint 10.00/10)
- [ ] Update documentation
- [ ] Commit changes with detailed message

### Post-Update Validation

- [ ] Container builds successfully
- [ ] All tools available in container
- [ ] Pylint reports maintain 10.00/10 score
- [ ] No new errors in workspace
- [ ] Git working tree clean

---

## Dependencies Reference

Current baked-in dependencies in `tools/.config/docker/Dockerfile`:

```dockerfile
RUN pip install --no-cache-dir \
    PyYAML>=6.0.1 \
    requests>=2.31.0 \
    click>=8.1.7 \
    rich>=13.7.0 \
    psycopg2-binary>=2.9.9 \
    qdrant-client>=1.7.0 \
    openai>=1.12.0 \          # ← Target for update to 2.8.1
    python-dotenv>=1.0.0 \
    colorlog>=6.8.2 \
    pre-commit>=3.4.0 \
    black==25.11.0 \
    isort==5.12.0 \            # ← Target for update to 7.0.0
    ruff==0.14.6 \
    sqlfluff==3.5.0
```

---

## Related Documents

- [Tools Container Documentation](../tools-container.md)
- [Docker Enhancements Branch](../../.github/branches/docker-enhancements.md)
- [Code Quality Standards](../../CONTRIBUTING.md)

## Next Review

After research phase completion and successful test branch validation.

---

**Last Updated**: 2025-11-24
**Reviewed By**: Development Team
**Next Action**: Begin isort 7.0.0 research and changelog review
