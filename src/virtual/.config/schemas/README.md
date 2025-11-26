# JSON Schemas for Configuration Validation

This directory contains JSON Schema definitions for validating YAML and JSON configuration files in the semantic-kernel-app project with comprehensive GPU/CUDA support.

## Available Schemas

| Schema                        | Description                                          | Usage                                        |
| ----------------------------- | ---------------------------------------------------- | -------------------------------------------- |
| `config.schema.json`          | General YAML configuration with GPU/CUDA definitions | `.config/*.yml` files                        |
| `docker-compose.schema.json`  | Docker Compose with NVIDIA GPU device support        | `docker-compose.yml`, `docker-compose.*.yml` |
| `github-workflow.schema.json` | GitHub Actions with self-hosted GPU runner support   | `.github/workflows/*.yml`                    |

## GPU/CUDA Schema Features

### config.schema.json

- `gpu_config` definition for CUDA settings
- `gpu_resources` for service-level GPU allocation
- `self_hosted_runner` for pre-configured GPU runner
- `python_environment` with CUDA/PyTorch support
- Environment variable validation (CUDA_VISIBLE_DEVICES, TORCH_CUDA_ARCH_LIST, etc.)

### docker-compose.schema.json

- `deviceSpec` for GPU device reservations
- `gpuConfig` for simplified GPU configuration
- NVIDIA runtime support (`runtime: nvidia`)
- Device capabilities validation (gpu, compute, utility)
- GPU memory and device ID configuration

### github-workflow.schema.json

- `selfHostedGpuRunner` definition (no token required)
- `runsOnConfig` with labels for GPU runners
- `containerConfig` with `--gpus all` option support
- Service container GPU access
- Workflow dispatch inputs for GPU parameters

## Usage

### In YAML Files

Add a schema reference comment at the top of your YAML file:

```yaml
# yaml-language-server: $schema=./.config/schemas/config.schema.json
```

### GPU-Enabled Service Example

```yaml
services:
  engine:
    gpu_enabled: true
    resources:
      gpu:
        enabled: true
        count: 1
        memory: "6G"
```

### Self-Hosted GPU Runner Example

```yaml
jobs:
  gpu-test:
    runs-on: self-hosted-gpu # Pre-configured, no token required
    steps:
      - name: Verify GPU
        run: nvidia-smi
```

### Docker Compose GPU Example

```yaml
services:
  embeddings:
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [[gpu, compute, utility]]
    environment:
      NVIDIA_VISIBLE_DEVICES: all
      CUDA_VISIBLE_DEVICES: "0"
```

### In VS Code

The YAML extension will automatically pick up schema references and provide:

- IntelliSense/autocomplete for GPU configuration
- Validation errors for invalid GPU settings
- Hover documentation for CUDA environment variables

### Schema Validation in CI

Schemas are validated during CI using the pre-commit hooks and yamllint configuration.

## Schema Standards

All schemas follow:

- JSON Schema Draft-07
- Semantic versioning
- Clear descriptions for all properties
- Required field validation
- Pattern validation for formatted strings (dates, versions, CUDA versions, etc.)
- GPU-specific enums and patterns

## Environment Configuration

GPU-related environment variables are documented in `.config/environment.yml`:

- `CUDA_VISIBLE_DEVICES` - GPU device selection
- `TORCH_CUDA_ARCH_LIST` - PyTorch CUDA architecture (e.g., "8.6")
- `PYTORCH_CUDA_ALLOC_CONF` - Memory allocation settings
- `NVIDIA_VISIBLE_DEVICES` - NVIDIA container device exposure
- `NVIDIA_DRIVER_CAPABILITIES` - Required driver capabilities

## Self-Hosted Runner Configuration

The self-hosted GPU runner is **pre-configured and registered**:

- Label: `self-hosted-gpu`
- Token required: **No** (already registered)
- GPU: RTX 3050 6GB
- CUDA: 13.0
- PyTorch: 2.9.1+cu130
- Compute capability: 8.6

## Related Configuration

- `.config/environment.yml` - Comprehensive environment variables
- `.config/services.yml` - Service configurations with GPU resources
- `.config/semantic-kernel.yml` - AI/ML configuration with CUDA settings
- `.config/infrastructure.yml` - Docker GPU runtime configuration
- `.yamllint.yml` - YAML linting rules
- `.editorconfig` - Editor formatting rules
- `.pre-commit-config.yaml` - Pre-commit validation hooks

## Contributing

When adding new configuration file types:

1. Create a schema in this directory
2. Include GPU/CUDA definitions if applicable
3. Add documentation to this README
4. Update the YAML Language Server configuration if needed
5. Test schema validation with sample YAML files
