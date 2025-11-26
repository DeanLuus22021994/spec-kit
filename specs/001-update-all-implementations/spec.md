# Feature Specification: Update All Implementations to Support Local/Virtual Architecture

**Feature Branch**: `001-update-all-implementations`
**Created**: 2025-11-26
**Status**: Draft
**Input**: User description: "Update all implementations to support the new src/local and src/virtual architecture."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Update Templates to Reflect New Architecture (Priority: P1)

The project templates used by the CLI must reflect the new architecture where infrastructure lives in `src/local` and application code lives in `src/virtual`.

**Why this priority**: The templates are the source of truth for new projects and plans. If they are outdated, the AI will generate incorrect plans.

**Independent Test**: Generate a new plan using `/speckit.plan` and verify the "Project Structure" section includes the Local/Virtual option.

**Acceptance Scenarios**:

1. **Given** the `plan-template.md` file, **When** inspected, **Then** it should include an option for the "Local/Virtual" structure (`src/local`, `src/virtual`).
2. **Given** the `tasks-template.md` file, **When** inspected, **Then** the "Path Conventions" section should mention `src/virtual/src` and `src/local`.

---

### User Story 2 - Update CLI Logic for Project Detection (Priority: P2)

The CLI commands (like `init` or `check`) might need to detect if a project is using the new structure.

**Why this priority**: To ensure the tools work correctly in the new environment.

**Independent Test**: Run `specify check` (or similar) in a project with the new structure and ensure it reports correctly.

**Acceptance Scenarios**:

1. **Given** a project with `src/local` and `src/virtual`, **When** running CLI commands, **Then** they should recognize the project structure.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `src/specify_cli/templates/plan-template.md` MUST include the `src/local` and `src/virtual` structure in the "Project Structure" section.
- **FR-002**: `src/specify_cli/templates/tasks-template.md` MUST include path conventions for the new structure.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Templates accurately reflect the new architecture.

