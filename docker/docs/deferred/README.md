# Deferred Items

**Purpose**: This directory contains deferred requirements, updates, and features that require additional research, planning, or resources before implementation.

## Directory Structure

```
deferred/
├── README.md                           # This file
├── devcontainer-validation-participant.md  # DevContainer validation service
└── python-package-updates.md           # Python dependency updates
```

## Document Format

All deferred items follow this standardized format:

### Header Metadata

```markdown
# [Title] - Deferred

**Status**: [Research Required | Blocked | Low Priority | Scheduled]
**Priority**: [Low | Medium | High | Critical]
**Created**: YYYY-MM-DD
**Category**: [Category1, Category2]
**Impact**: [Affected areas/components]
```

### Required Sections

1. **Overview**: Brief description of the deferred item
2. **Current State**: What exists today
3. **Proposed Solution** or **Deferred Updates**: What needs to change
4. **Impact Areas**: What components/files are affected
5. **Required Research** or **Testing Steps**: Checklist of investigation needed
6. **Acceptance Criteria**: Definition of done
7. **Estimated Effort**: Time estimate
8. **Related Documents**: Links to relevant documentation
9. **Next Review**: When to revisit

## Status Definitions

- **Research Required**: Needs investigation before implementation
- **Blocked**: Waiting on external dependency or prerequisite
- **Low Priority**: Not critical, can be delayed indefinitely
- **Scheduled**: Planned for specific milestone/release

## Priority Levels

- **Low**: Nice-to-have, implement when convenient
- **Medium**: Should implement in next 1-2 quarters
- **High**: Should implement in next month
- **Critical**: Blocking other work, implement ASAP

## Categories

- **Dependencies**: Package/library updates
- **Infrastructure**: DevContainer, Docker, CI/CD
- **Developer Experience**: Tooling, workflows, automation
- **Code Quality**: Linting, testing, formatting
- **Documentation**: Docs improvements
- **Security**: Security improvements
- **Performance**: Optimization work
- **Features**: New functionality

## Review Cadence

- **High/Critical Priority**: Weekly review
- **Medium Priority**: Monthly review
- **Low Priority**: Quarterly review

## Graduation Criteria

A deferred item can be moved from `docs/deferred/` to active implementation when:

1. All research completed
2. Dependencies resolved
3. Resources allocated
4. Acceptance criteria defined
5. Implementation approach approved

### Graduation Destinations

- `docs/architecture/` - Architectural decisions and designs
- `docs/development/` - Implementation guides
- Feature branch in active development
- Issue/ticket in project tracking system

## Contributing

When adding a new deferred item:

1. Use the standard format template
2. Assign appropriate status, priority, and categories
3. Link to related documents
4. Add to this README index
5. Update review schedule if high/critical priority

## Current Deferred Items

| Document                                                                        | Status            | Priority | Category                             | Next Review |
| ------------------------------------------------------------------------------- | ----------------- | -------- | ------------------------------------ | ----------- |
| [DevContainer Validation Participant](./devcontainer-validation-participant.md) | Research Required | Medium   | Infrastructure, Developer Experience | 2025-12-01  |
| [Python Package Updates](./python-package-updates.md)                           | Research Required | Medium   | Dependencies, Code Quality           | 2025-12-01  |

---

**Last Updated**: 2025-11-24
