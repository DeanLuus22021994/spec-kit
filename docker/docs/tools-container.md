# Python Tools Container

**Purpose:** Isolated Python environment for running CLI tools, documentation generators, and code quality checks without polluting the host system with cache files.

## Features

- **Base Image:** `python:3.14-slim` (minimal footprint)
- **Non-root User:** `toolsuser:1001` (security best practice)
- **Baked Dependencies:** All Python packages pre-installed in image for zero-latency execution
- **Cache Management:** Dedicated directories for `.mypy_cache`, `.pytest_cache`, `__pycache__`
- **No Cache Pollution:** `PYTHONDONTWRITEBYTECODE=1` prevents bytecode generation on host

## Tools Included

### Application Tools

- `cli.py` - Command-line interface for project operations
- `docgen.py` - Documentation generation

### Code Quality Tools (Baked-In)

- `black==25.11.0` - Code formatting
- `isort==5.12.0` - Import sorting
- `ruff==0.14.6` - Fast Python linter
- `sqlfluff==3.5.0` - SQL linting
- `pre-commit>=3.4.0` - Git hook management

### Runtime Dependencies (Baked-In)

- `PyYAML>=6.0.1` - YAML parsing
- `requests>=2.31.0` - HTTP requests
- `click>=8.1.7` - CLI framework
- `rich>=13.7.0` - Terminal formatting
- `psycopg2-binary>=2.9.9` - PostgreSQL connectivity
- `qdrant-client>=1.7.0` - Vector database
- `openai>=1.12.0` - OpenAI integration
- `python-dotenv>=1.0.0` - Environment management
- `colorlog>=6.8.2` - Colored logging

## Building

```bash
# From project root (recommended)
docker build -f tools/.config/docker/Dockerfile -t semantic-kernel-tools:latest tools/

# From tools/ directory
cd tools && docker build -f .config/docker/Dockerfile -t semantic-kernel-tools:latest .
```

## Running

### CLI Tool

```bash
docker run --rm -v $(pwd):/workspace semantic-kernel-tools:latest python cli.py --help
```

### Documentation Generator

```bash
docker run --rm -v $(pwd):/workspace semantic-kernel-tools:latest python docgen.py
```

### Pylint Analysis

```bash
docker run --rm -v $(pwd):/workspace semantic-kernel-tools:latest \
    python -m pylint /workspace/semantic /workspace/tools --rcfile=/workspace/.pylintrc
```

### Black Formatting

```bash
docker run --rm -v $(pwd):/workspace semantic-kernel-tools:latest \
    black /workspace/semantic /workspace/tools
```

### Interactive Shell

```bash
docker run -it --rm -v $(pwd):/workspace semantic-kernel-tools:latest bash
```

## Cache Directories

All Python cache files are contained within the container:

- `/app/tools/.mypy_cache/` - MyPy type checking cache
- `/app/tools/.pytest_cache/` - Pytest test cache
- `/app/tools/__pycache__/` - Python bytecode cache

**Host Pollution Prevention:**

- `PYTHONDONTWRITEBYTECODE=1` - No `.pyc` files written
- Cache directories owned by `toolsuser:1001`
- `.dockerignore` excludes existing cache from image builds

## Integration with Docker Compose

Add to `docker-compose.yml`:

```yaml
tools:
  build:
    context: ./tools
    dockerfile: .config/docker/Dockerfile
  image: semantic-kernel-tools:latest
  container_name: semantic-kernel-tools
  user: "1001:1001"
  volumes:
    - ./:/workspace:ro
    - tools-cache:/app/tools/.mypy_cache
    - tools-pytest:/app/tools/.pytest_cache
  environment:
    - PYTHONUNBUFFERED=1
    - PYTHONDONTWRITEBYTECODE=1
  command: tail -f /dev/null
```

Add volumes:

```yaml
volumes:
  tools-cache:
  tools-pytest:
```

## Health Check

Container includes health check that runs every 30s:

```bash
python -c "import sys; sys.exit(0)"
```

## Security

- **Non-root execution:** All processes run as `toolsuser:1001`
- **Minimal dependencies:** Only essential system packages (git)
- **No cache-dir:** pip installs without caching to reduce image size
- **Clean apt lists:** Removed after package installation

## File Structure

```
tools/
├── .config/
│   ├── copilot/         # GitHub Copilot context files
│   │   ├── index.yml    # Master context index
│   │   ├── docker.yml   # Container patterns and workflows
│   │   └── scripts.yml  # Automation script documentation
│   ├── docker/
│   │   ├── Dockerfile   # Container definition with baked-in dependencies
│   │   └── .dockerignore # Build exclusions (cache files, venv, etc.)
│   └── scripts/         # Automation scripts
│       ├── lint.sh      # Code quality checks
│       └── precommit-autoupdate.sh # Pre-commit hook updates
├── .gitignore          # Prevent Python cache pollution
├── cli.py              # CLI tool
├── docgen.py           # Documentation generator
└── requirements.txt    # Python dependencies list
```

**Note:** Dependencies are baked directly into `.config/docker/Dockerfile` for instant availability. The `requirements.txt` file is maintained for reference and IDE support.

## Troubleshooting

**Cache files appearing on host:**

- Verify `PYTHONDONTWRITEBYTECODE=1` is set
- Check container user is `toolsuser:1001`
- Ensure volume mounts are correct

**Permission errors:**

- Container runs as UID 1001
- Match host user or use Docker user mapping

**Missing tools:**

- Rebuild image: `docker build --no-cache -f tools/.config/docker/Dockerfile -t semantic-kernel-tools:latest tools/`
- Check `.config/docker/Dockerfile` RUN pip install section has all required dependencies

---

**Last Updated:** 2025-11-24
**Image Size:** 661MB (with all dependencies baked-in)
**Python Version:** 3.11
**Build Strategy:** Zero-latency (dependencies pre-installed, no runtime pip install)
