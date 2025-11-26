# Copilot Patterns and Workflows

**Purpose**: Repository-specific patterns, workflows, and conventions for efficient Copilot interactions.

---

## Code Quality Workflows

**Reference**: `.config/copilot/standards/code-quality.yml`

### Quick Commands

```bash
# Combined report (semantic/ + tools/)
VS Code Task: "Generate Pylint Report"

# Tools-only report
VS Code Task: "Generate Pylint Tools Report"

# Pre-commit hooks
VS Code Task: "Run Pre-commit Hooks"
```

**Target**: 10.00/10 pylint rating | **Reports**: `reports/pylint_report.txt`, `reports/pylint_tools_report.txt`

---

## GitHub CLI Patterns

**Reference**: `.config/copilot/workflows/github-cli.yml` | [docs/github-cli-reference.md](../github-cli-reference.md)

### Critical Field Names

- ✅ `defaultBranchRef` (NOT `defaultBranch`)
- ✅ `headRefName`, `baseRefName`, `statusCheckRollup`

### Quick Commands

```yaml
# See .config/copilot/workflows/github-cli.yml → common_commands
Check PR:     gh pr list --head $(git branch --show-current)
Default Branch: gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
PR Status:    gh pr view --json number,state,reviewDecision,statusCheckRollup
Create PR:    gh pr create --base main --head feature --title "feat: description"

# VS Code Tasks: "GitHub: Check PR", "GitHub: Get Default Branch", "GitHub: View PR"
```

---

## Deferred Items Workflow

**Reference**: `.config/copilot/workflows/deferred-items.yml` | [docs/deferred/README.md](../deferred/README.md)

### When to Defer

See `.config/copilot/workflows/deferred-items.yml` → `when_to_defer`

### Quick Format

```yaml
# Required Metadata (see .config/copilot/workflows/deferred-items.yml)
status: deferred|in-progress|completed
priority: low|medium|high|critical
effort: 1-2 hours|2-3 hours|3-4 hours|1+ days
category: dependencies|features|infrastructure|documentation

# Required Sections (see .config/copilot/workflows/deferred-items.yml → required_sections)
1. Summary | 2. Current State | 3. Proposed Changes
4. Breaking Changes | 5. Update Strategy | 6. Testing
7. Acceptance Criteria | 8. References
```

### Graduation Process

1. Update `status: in-progress` → 2. Create feature branch → 3. Implement → 4. Test → 5. Mark `completed`

---

## Tools Container Usage

**Reference**: `.config/copilot/workflows/tools-container.yml` | [docs/tools-container.md](../tools-container.md)

**Specs**: `semantic-kernel-tools:latest` (661MB, python:3.14-slim, all dependencies baked)

### Quick Commands

```yaml
# See .config/copilot/workflows/tools-container.yml → common_commands
CLI Config: docker run --rm -v ${PWD}:/workspace semantic-kernel-tools:latest python tools/cli.py --show-config
Generate Docs: docker run --rm -v ${PWD}:/workspace semantic-kernel-tools:latest python tools/docgen.py
Pre-commit: docker run --rm -v ${PWD}:/workspace semantic-kernel-tools:latest pre-commit run --all-files
Pylint: docker run --rm -v ${PWD}:/workspace semantic-kernel-tools:latest python -m pylint semantic/ tools/
# VS Code Tasks: "Tools: CLI Config", "Tools: Generate Documentation", "Run Pre-commit Hooks"
```

**Cache Isolation**: `.mypy_cache` in container, `PYTHONDONTWRITEBYTECODE=1`, zero host pollution

---

## Documentation Organization

**Reference**: `.config/copilot/patterns/documentation.yml`

### Structure

```yaml
# See .config/copilot/patterns/documentation.yml → structure
Reference: docs/*.md (github-cli-reference.md, tools-container.md)
Development: docs/development/*.md (guides, patterns, workflows)
Deferred: docs/deferred/*.md (standardized deferred items)
CLI: docs/cli/*.md (CLI tool documentation)
Configuration: docs/configuration/*.md (YAML file docs)
Dockerfiles: docs/dockerfiles/*.md (Dockerfile docs)
```

### When to Create Docs

See `.config/copilot/patterns/documentation.yml` → `when_to_create`

**Always update** `docs/mkdocs.yml` navigation when adding new documentation

---

## Naming Conventions

**Reference**: `.config/copilot/patterns/version-control.yml`

### Quick Reference

```yaml
# Branches (see .config/copilot/patterns/version-control.yml → branch_naming)
feature/{name} | fix/{name} | docs/{topic} | refactor/{component} | test/{type}

# Commits (see .config/copilot/patterns/version-control.yml → commit_format)
<type>(<scope>): <description>
Types: feat|fix|docs|refactor|test|chore|perf

# Files
Python:    snake_case.py
C#:        PascalCase.cs
Docs:      kebab-case.md
Config:    kebab-case.yml or lowercase.yml
```

---

## Common Copilot Interactions

### "Implement new feature X"

1. **Check for TODOs**: Search codebase for related TODOs
2. **Review architecture**: Check `docs/index.md` for context
3. **Create branch**: `git checkout -b feature/{feature-name}`
4. **Generate code**: Follow `.github/copilot-instructions.md` standards
5. **Write tests**: Add unit/integration tests
6. **Update docs**: Document in `docs/` if needed
7. **Commit**: Use conventional commit format

### "Update dependency Y"

1. **Check breaking changes**: Review changelog
2. **Estimate effort**: < 1 hour = update now, > 1 hour = defer
3. **If deferring**: Create `docs/deferred/{dependency}.md`
4. **If updating**: Update Dockerfile/package.json/requirements.txt
5. **Run tests**: Ensure no regressions
6. **Generate reports**: Pylint/npm audit
7. **Commit**: `chore(deps): update Y to version Z`

### "Debug issue Z"

1. **Check logs**: `docker-compose logs -f {service}`
2. **Review errors**: Check VS Code Problems panel
3. **Search codebase**: Use semantic search for relevant code
4. **Check docs**: Review `docs/` for known issues
5. **Apply fix**: Follow coding standards
6. **Add tests**: Prevent regression
7. **Commit**: `fix({component}): resolve Z issue`

### "Generate documentation"

1. **Determine category**: Reference/Development/Deferred?
2. **Choose location**: `docs/{category}/{file}.md`
3. **Follow format**: Markdown with code examples
4. **Update navigation**: Edit `docs/mkdocs.yml`
5. **Validate**: Check for broken links
6. **Commit**: `docs: add {topic} documentation`

---

## Automation Patterns

**Reference**: `.config/copilot/standards/code-quality.yml`, `.config/copilot/references/vscode-tasks.yml`

### Pre-commit Hooks

**Runs on** `git commit`: black, isort, ruff, sqlfluff, prettier, eslint

**Manual**: `pre-commit run --all-files` or VS Code Task: "Run Pre-commit Hooks"

### VS Code Tasks

**Access**: `Ctrl+Shift+P` → `Tasks: Run Task`

```yaml
# See .config/copilot/references/vscode-tasks.yml → categories
Build:   Build Solution | Build Backend | Build Engine
Docker:  Docker: Up | Docker: Down | Docker: Logs
Quality: Generate Pylint Report | Run Pre-commit Hooks
GitHub:  Check PR | Get Default Branch | View PR
Tools:   CLI Config | Generate Documentation
```

### Docker Compose

```bash
docker-compose up -d          # Start all services
docker-compose logs -f {svc}  # View logs
docker-compose build {svc}    # Rebuild service
docker ps                     # Health checks
```

---

## Troubleshooting Patterns

**Reference**: `.config/copilot/patterns/troubleshooting.yml`

```yaml
# Quick Solutions
CRLF Issues:        .editorconfig enforces end_of_line=lf | Verify: git diff
Pylint Drop:        VS Code Task: "Generate Pylint Report" → Fix → Re-run
Docker Build Fail:  Check Dockerfile | Verify base image | Run --no-cache | Check .dockerignore
GitHub CLI Error:   Reference docs/github-cli-reference.md for correct field names
Tools Container:    docker build -f dockerfiles/tools.Dockerfile -t semantic-kernel-tools:latest .
```

---

## Best Practices

**Reference**: `.config/copilot/standards/best-practices.yml`

```yaml
1.  Check .config/copilot/*.yml before creating new documentation
2.  Use VS Code tasks instead of typing commands manually
3.  Run pylint before commits to maintain 10.00/10
4.  Reference docs/github-cli-reference.md for field names
5.  Defer breaking changes with docs/deferred/*.md
6.  Isolate Python tools in container
7.  Follow commit conventions for clear history
8.  Update docs/mkdocs.yml when adding docs
9.  Use timestamped reports for traceability
10. Document architectural decisions
```

---

**Last Updated**: 2025-01-27
**Maintained By**: Development Team
**Related Files**:

- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) - Copilot configuration
- [.config/copilot/index.yml](../../.config/copilot/index.yml) - Context index (⭐ primary reference)
- [docs/github-cli-reference.md](../github-cli-reference.md) - GitHub CLI fields
- [docs/tools-container.md](../tools-container.md) - Tools container details
- [docs/deferred/README.md](../deferred/README.md) - Deferred items format
