---
title: Python CLI Tool
description: Command-line interface for managing semantic kernel operations
---

# Python CLI Tool

The Python CLI tool provides command-line access to semantic kernel operations, embeddings, and AI workflows.

## Location

**File**: `tools/cli.py`
**Configuration**: `.config/cli.yml`
**Dependencies**: `tools/requirements.txt`

## Overview

A minimal Python CLI that leverages YAML configuration for managing:

- Semantic kernel operations
- Plugin and skill management
- Embedding generation and vector search
- Configuration management

## Installation

### Install Dependencies

```bash
cd tools
pip install -r requirements.txt
```

### Required Packages

```
PyYAML>=6.0.1          # YAML parsing
requests>=2.31.0        # HTTP requests
click>=8.1.7            # CLI framework
rich>=13.7.0            # Terminal formatting
psycopg2-binary>=2.9.9  # PostgreSQL
qdrant-client>=1.7.0    # Vector database
openai>=1.12.0          # OpenAI API
python-dotenv>=1.0.0    # Environment variables
colorlog>=6.8.2         # Colored logging
```

## Usage

### Basic Commands

#### Show Configuration

```bash
python tools/cli.py --show-config
```

Displays the current configuration from `.config/cli.yml` in YAML format.

#### List Available Commands

```bash
python tools/cli.py --list-commands
```

Shows all available commands and subcommands defined in the configuration.

#### Use Custom Config File

```bash
python tools/cli.py --config /path/to/custom-cli.yml --show-config
```

### Output Formats

Specify output format with `--format`:

```bash
# JSON format (default)
python tools/cli.py --list-commands --format json

# YAML format
python tools/cli.py --list-commands --format yaml

# Table format
python tools/cli.py --list-commands --format table
```

## Configuration

The CLI tool loads configuration from `.config/cli.yml`. See [YAML Configuration Files](../configuration/yaml-files.md#cli-configuration) for details.

### Environment Variables

Required environment variables:

```bash
# Database
export DB_PASSWORD="your_password"

# OpenAI
export OPENAI_API_KEY="sk-..."

# API Authentication
export SK_API_TOKEN="your_token"
```

## API Methods

### Configuration Access

#### Get API Endpoint

```python
from tools.cli import SemanticKernelCLI

cli = SemanticKernelCLI()
backend_url = cli.get_api_endpoint("backend")
# Returns: "http://localhost:5000"
```

#### Get OpenAI Config

```python
openai_config = cli.get_openai_config()
# Returns: {
#   "api_key": "sk-...",
#   "model": "gpt-4",
#   "embedding_model": "text-embedding-3-small",
#   "max_tokens": 2000,
#   "temperature": 0.7
# }
```

#### Get Database Config

```python
db_config = cli.get_database_config()
# Returns: {
#   "host": "localhost",
#   "port": 5432,
#   "database": "semantic_kernel",
#   "user": "user",
#   "password": "..."
# }
```

#### Get Feature Flags

```python
features = cli.get_feature_flags()
# Returns: {
#   "async_operations": true,
#   "batch_processing": true,
#   "auto_retry": true,
#   "telemetry": true,
#   "caching": true
# }
```

### Output Methods

#### JSON Output

```python
data = {"status": "success", "message": "Operation completed"}
cli.output(data, format="json")
```

#### YAML Output

```python
cli.output(data, format="yaml")
```

## Available Commands

As defined in `.config/cli.yml`:

### Kernel Management

```bash
sk-cli kernel create <name>
sk-cli kernel list
sk-cli kernel delete <name>
sk-cli kernel status <name>
```

### Plugin Management

```bash
sk-cli plugins install <plugin>
sk-cli plugins list
sk-cli plugins remove <plugin>
sk-cli plugins update <plugin>
```

### Skill Management

```bash
sk-cli skills add <skill>
sk-cli skills list
sk-cli skills invoke <skill> <args>
sk-cli skills test <skill>
```

### Embeddings Operations

```bash
sk-cli embeddings generate <text>
sk-cli embeddings search <query>
sk-cli embeddings index <documents>
sk-cli embeddings query <vector>
```

### Configuration Management

```bash
sk-cli config show
sk-cli config set <key> <value>
sk-cli config reset
```

## Example Usage

### Python Script Example

```python
#!/usr/bin/env python3
from tools.cli import SemanticKernelCLI

# Initialize CLI
cli = SemanticKernelCLI()

# Get API endpoints
backend = cli.get_api_endpoint("backend")
embeddings = cli.get_api_endpoint("embeddings")

# Get database config
db_config = cli.get_database_config()

# Check feature flags
if cli.get_feature_flags()["caching"]:
    print("Caching is enabled")

# Output data
result = {
    "backend": backend,
    "embeddings": embeddings,
    "database": db_config["database"]
}
cli.output(result, format="json")
```

### Shell Integration

Add to `.bashrc` or `.zshrc`:

```bash
alias sk="python /path/to/tools/cli.py"

# Then use:
sk --list-commands
sk --show-config
```

## Logging

The CLI tool uses Python's logging module configured from YAML:

```yaml
logging:
  level: "info"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/cli.log"
  max_size_mb: 10
  backup_count: 5
```

### Log Levels

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

## Code Structure

### Main Class

```python
class SemanticKernelCLI:
    def __init__(self, config_path: Optional[str] = None)
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]
    def _setup_logging(self) -> None
    def get_api_endpoint(self, service: str) -> str
    def get_openai_config(self) -> Dict[str, Any]
    def get_database_config(self) -> Dict[str, Any]
    def output(self, data: Any, format: Optional[str] = None) -> None
    def show_config(self) -> None
    def list_commands(self) -> None
    def get_feature_flags(self) -> Dict[str, bool]
```

### Entry Point

```python
def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    cli = SemanticKernelCLI(config_path=args.config)
    # Handle commands...
```

## Error Handling

The CLI includes comprehensive error handling:

```python
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return cast(Dict[str, Any], config)
except FileNotFoundError:
    print(f"Error: Configuration file not found: {config_path}")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error parsing YAML configuration: {e}")
    sys.exit(1)
```

## Development

### Running Tests

```bash
# Run unit tests
pytest tests/test_cli.py

# Run with coverage
pytest --cov=tools tests/
```

### Code Quality

The Python code follows:

- PEP 8 style guide
- 150 character line length (configured in `pyproject.toml`)
- Type hints for all functions
- Comprehensive docstrings

### Configuration in pyproject.toml

```toml
[tool.black]
line-length = 150
target-version = ['py313']  # Python 3.14.0

[tool.isort]
profile = "black"
line_length = 150

[tool.flake8]
max-line-length = 150
```

## Related Documentation

- [YAML Configuration Files](../configuration/yaml-files.md)
- [Development Setup](../development/setup.md)
- [API Reference](../api/backend.md)
