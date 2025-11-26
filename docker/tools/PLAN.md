## Plan: Migrate Custom MTA Rules to Tools Directory (Updated)

Integrate MTA/Kantra YAML validation into tools directory with containerized CLI, automation scripts, and comprehensive documentation following Red Hat MTA 7.2 specifications and repository patterns.

### Steps

1. **Create `tools/.config/validation/` directory structure** - Establish subdirectory `validation/` under .config with child directories: `rules/` (MTA rule files), reports (HTML/YAML outputs), and `test-data/` (sample files for rule testing). Mirrors pattern of scripts, `docker/`, `copilot/`.

2. **Move and update rule files to `tools/.config/validation/rules/`** - Relocate all 7 files from [`custom-rules/`](c:\Users\Dean\source\semantics\semantic-kernel-app\custom-rules) to new location, updating `ruleset.yaml` metadata with proper `config_references` to yaml-best-practices.yml, fix all relative file paths in `README.md`, and ensure rule `ruleID` values follow Red Hat naming: `yaml-{category}-{specific-check}`.

3. **Install Kantra CLI in Dockerfile** - Add Kantra binary download from `quay.io/konveyor/kantra:latest` container image using multi-stage build pattern, extract `/usr/local/bin/kantra` binary, verify with `kantra --version`, and bake validation rules into container at `/workspace/.config/validation/rules/` (zero file copy latency pattern).

4. **Create `tools/.config/scripts/validate-yaml.sh` automation script** - Implement bash script with: `set -euo pipefail` error handling, `kantra analyze --input . --output reports/validation/ --rules .config/validation/rules/ --enable-default-rulesets=false` command, report generation to `tools/.config/validation/reports/`, color-coded console output (green=pass, red=fail), and exit codes (0=success, 1=mandatory failures, 2=optional issues).

5. **Update Dockerfile with complete integration** - Add `COPY .config/validation/rules/ /workspace/.config/validation/rules/`, create non-root `toolsuser:1001` ownership, create named volume `validation-reports:/workspace/.config/validation/reports/` for persistence, install Podman 4+ as Kantra dependency (or use host podman via socket mount), and configure `ENTRYPOINT` to support `validate-yaml` command.

6. **Create `tools/.config/copilot/validation.yml` comprehensive context** - Document: Kantra CLI vs legacy mta-cli (Kantra is new unified CLI), analysis modes (containerless with `--run-local` vs hybrid), output formats (HTML static reports, YAML analysis files, JSON with `--json-output`), rule testing workflow with `kantra test`, label selectors (`--label-selector="category=mandatory"`), and cross-reference to `.config/copilot/yaml-best-practices.yml`.

7. **Update root Makefile with validation targets** - Add `validate-yaml:` target calling `docker run --rm -v $(pwd):/workspace semantic-kernel-tools:latest bash .config/scripts/validate-yaml.sh`, `validate-yaml-mandatory:` with `--label-selector="category=mandatory"` filter, `validate-yaml-report:` opening HTML report in browser, following existing `lint` and `lint-report` pattern.

8. **Create GitHub Actions workflow `.github/workflows/validate-yaml.yml`** - Implement CI/CD workflow: trigger on push/PR to YAML files (`**/*.yml`, `**/*.yaml`), download Kantra from `quay.io/konveyor/kantra:latest`, run `kantra analyze --rules custom-rules/ --label-selector="category=mandatory"`, upload HTML report as artifact, fail build on mandatory rule violations, and add status badge to README.

### Further Considerations

1. **Kantra vs MTA CLI relationship** - Kantra is the new unified CLI (replaces `mta-cli`/`windup-cli`). Should update all documentation from "mta-cli" to "kantra" for accuracy? Red Hat MTA 7.2 docs still reference both—use Kantra for future-proofing.

2. **Podman/Docker dependency strategy** - Kantra requires Podman 4+/Docker 24+. Options: Install in Dockerfile (nested container complexity) / Mount host podman socket (`/run/podman/podman.sock`) / Use `--run-local` containerless mode (requires analyzer-lsp providers on host)?

3. **Rule testing integration depth** - Kantra has `kantra test` subcommand for rule validation. Should create `.test.yaml` files in `tools/.config/validation/test-data/` with sample violations for each rule category or rely on manual testing?

4. **Pre-commit hook integration** - Should YAML validation run on every commit via .pre-commit-config.yaml (potentially slow for large repos) or only in CI/CD pipeline or both with `--label-selector` filtering for pre-commit?

5. **Report format and storage** - Kantra outputs: HTML static report (human), `output.yaml` (machine), `dependencies.yaml` (deps). Should commit reports to Git (bloat) / Upload as CI artifacts only / Store in named volume for local review?
