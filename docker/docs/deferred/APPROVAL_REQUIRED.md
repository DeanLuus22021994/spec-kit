# Deferred Items Requiring Approval

**Last Updated**: 2025-11-24
**Status**: ⏳ Pending Management Review

---

## Cost Implications Summary

Items requiring budget approval before implementation due to cloud service testing costs, extended development time, or infrastructure requirements.

---

## 1. OpenAI SDK Upgrade (1.12.0 → 2.8.1)

### Overview

**Current Version**: openai 1.12.0
**Target Version**: openai 2.8.1
**Service Impact**: semantic/embeddings/ (FastAPI service)
**Priority**: Medium
**Risk**: High (breaking API changes)

### Cost Breakdown

| Item                    | Estimated Cost   | Justification                                                  |
| ----------------------- | ---------------- | -------------------------------------------------------------- |
| **OpenAI API Testing**  | $50-100          | Integration testing with live API (100-200 embedding requests) |
| **Staging Environment** | $25-50/month     | Azure Container Instance for pre-production validation         |
| **Development Time**    | 6-7 hours × rate | Senior developer research, coding, testing                     |
| **Load Testing**        | $20-30           | OpenAI API calls during performance validation                 |
| **Monitoring (24hr)**   | $10-15           | Application Insights for staging observation                   |
| **Total (One-time)**    | $105-195         | Upfront testing and validation                                 |
| **Total (Monthly)**     | $25-50           | Ongoing staging infrastructure                                 |

### Why Approval Needed

1. **Breaking API Changes**: Requires 40-50 line rewrite in production service
2. **No Test Coverage**: Missing unit/integration tests for embeddings service
3. **Live API Required**: Cannot validate without actual OpenAI API calls (costs money)
4. **Staging Environment**: Need safe environment before production deployment
5. **Business Critical**: Embeddings service is in hot path for semantic search

### Prerequisites (Not Met)

- ❌ Unit tests for embeddings service
- ❌ Integration test suite with mocked/real OpenAI API
- ❌ Staging environment (Azure Container Instance)
- ❌ Performance baseline metrics
- ❌ Rollback plan documented
- ❌ API cost budget allocated

### Technical Details

**Code Changes Required**:

```python
# OLD (1.x) - Current Implementation
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")
response = openai.Embedding.create(
    model="text-embedding-3-small",
    input="text to embed"
)
embedding = response['data'][0]['embedding']

# NEW (2.x) - Required Migration
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = await client.embeddings.create(
    model="text-embedding-3-small",
    input="text to embed"
)
embedding = response.data[0].embedding  # Pydantic model, not dict
```

**Files Affected**:

- `semantic/embeddings/main.py` (40-50 lines changed)
- `dockerfiles/embeddings.Dockerfile` (dependency version)
- `tools/.config/docker/Dockerfile` (dependency version)

**Breaking Changes**:

1. Client-based API (must instantiate `OpenAI()`)
2. Response objects (Pydantic models, not dicts)
3. Async patterns (`AsyncOpenAI()` for FastAPI)
4. Error handling (new exception classes)
5. Streaming API changes

### Business Impact

**Current State**:

- Embeddings service stable on openai 1.12.0
- Zero downtime since deployment
- No security vulnerabilities reported

**Risk of Upgrade**:

- Service downtime during deployment
- Potential API behavior changes
- Unknown performance implications
- Rollback complexity (code changes, not just config)

**Risk of Deferral**:

- Missing newer features (streaming improvements)
- Security patches in 2.x line
- Eventually forced upgrade (1.x EOL)

### Recommended Timeline

**If Approved**:

1. **Week 1-2**: Create test infrastructure (unit + integration tests)
2. **Week 2-3**: Set up staging environment + baseline metrics
3. **Week 3**: Research + code migration (6-7 hours dev time)
4. **Week 4**: Testing + validation ($50-100 API costs)
5. **Week 5**: Staging deployment + 24hr monitoring ($10-15)
6. **Week 6**: Production deployment + rollback readiness

**Total Duration**: 6 weeks
**Total Cost**: $105-195 (one-time) + $25-50/month (staging)

**If Deferred**:

- Remain on openai 1.12.0 (stable, working)
- Monitor for security advisories
- Revisit in Q1 2026 when test infrastructure mature
- **Cost Savings**: $105-195 + $150-300 (6 months staging)

### Decision Required

**Options**:

1. ✅ **Approve with Budget** ($105-195 + staging costs)

   - Proceed with full implementation plan
   - Allocate API testing budget
   - Set up staging environment
   - Timeline: 6 weeks to production

2. ⏸️ **Defer to Q1 2026** (Cost savings: $105-195 immediate)

   - Complete test infrastructure first (P1 priority)
   - Add embeddings service to integration tests
   - Establish baseline metrics
   - Revisit after test coverage mature

3. ❌ **Reject Permanently** (Stay on 1.12.0)
   - Monitor for security vulnerabilities
   - Plan forced upgrade only if critical patch needed
   - Accept technical debt

### Recommendation

**⏸️ DEFER TO Q1 2026**

**Reasoning**:

- Current version (1.12.0) is stable and secure
- Test infrastructure incomplete (missing unit tests)
- No staging environment exists yet
- Higher priority work: create missing test projects (P1)
- Cost savings: $105-195 immediate + $150-300 (6mo staging)
- Better ROI: invest in test infrastructure first

**Action Items** (If Deferred):

1. Complete P1 priority: Create missing test projects (4-6hr)
2. Add embeddings service to integration test suite (2-3hr)
3. Document baseline performance metrics (1hr)
4. Set up staging environment (2-3hr)
5. Revisit openai 2.8.1 upgrade in Q1 2026 with proper foundation

---

## Approval Process

**Approver**: [Engineering Manager / Tech Lead]
**Date Submitted**: 2025-11-24
**Expected Response**: [Timeline]

**Approval Criteria**:

- [ ] Budget allocated for OpenAI API testing ($50-100)
- [ ] Budget allocated for staging environment ($25-50/month)
- [ ] Development time approved (6-7 hours)
- [ ] Timeline acceptable (6 weeks to production)
- [ ] Risk assessment reviewed and accepted
- [ ] Prerequisites completion plan approved

**Signatures**:

- [ ] Engineering Manager: ********\_******** Date: **\_\_\_**
- [ ] Product Owner: ********\_******** Date: **\_\_\_**
- [ ] Finance/Budget Approver: ********\_******** Date: **\_\_\_**

---

## Status Tracking

**Current Status**: ⏳ Pending Review
**Last Updated**: 2025-11-24
**Next Review Date**: [TBD]

**Status History**:

- 2025-11-24: Initial submission, recommendation to defer to Q1 2026
- [Future updates here]

---

## References

- Research findings: `docs/deferred/RESEARCH_FINDINGS.md`
- Testing plan: `docs/deferred/python-package-updates.md`
- Affected service: `semantic/embeddings/main.py`
- OpenAI migration guide: https://github.com/openai/openai-python/blob/main/CHANGELOG.md
