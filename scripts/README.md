# SpecKit Scripts

This directory contains the automation scripts for the SpecKit framework. The scripts are available in both Bash (for Linux/macOS/WSL) and PowerShell (for Windows).

## Architecture

The scripts are designed with a modular architecture to ensure consistency, maintainability, and robust error handling.

### Bash (`scripts/bash/`)

*   **`lib/speckit.sh`**: The core library that initializes logging, error handling, and sources other modules. All scripts source this file.
*   **`lib/common.sh`**: Contains shared functions for path resolution, git operations, and file checks.
*   **`lib/config.sh`**: Centralized configuration for file paths, directory names, and limits.
*   **`lib/logger.sh`**: Standardized logging functions (`logger_info`, `logger_success`, `logger_warn`, `logger_error`).

### PowerShell (`scripts/powershell/`)

*   **`Modules/SpecKit/`**: A PowerShell module that encapsulates the core logic.
    *   **`SpecKit.psm1`**: The module manifest that loads classes and public functions.
    *   **`Classes/Logger.ps1`**: Defines the `SpecKitLogger` class.
    *   **`Public/Invoke-SpecKitBlock.ps1`**: A wrapper function that handles error catching and logging context.
    *   **`Public/Common.ps1`**: Shared utility functions.
    *   **`Public/Config.ps1`**: Centralized configuration.

## Usage

### Creating a New Feature

**Bash:**
```bash
./scripts/bash/create-new-feature.sh "My New Feature"
```

**PowerShell:**
```powershell
./scripts/powershell/create-new-feature.ps1 "My New Feature"
```

### Updating Agent Context

**Bash:**
```bash
./scripts/bash/update-agent-context.sh [agent_type]
```

**PowerShell:**
```powershell
./scripts/powershell/update-agent-context.ps1 [agent_type]
```

### Infrastructure Management

*   `start-local.sh` / `start-local.ps1`: Starts local infrastructure (DB, Redis, etc.).
*   `start-virtual.sh` / `start-virtual.ps1`: Starts the virtual application environment.
*   `stop-all.sh` / `stop-all.ps1`: Stops all running services.

## Development

When adding new scripts:
1.  **Bash**: Source `lib/speckit.sh` and wrap your main logic in a function passed to `invoke_speckit_block`. Use configuration variables from `lib/config.sh`.
2.  **PowerShell**: Import `common.ps1` and wrap your logic in `Invoke-SpecKitBlock`. Use `Get-SpecKitConfig` to access configuration.
