#!/usr/bin/env pwsh
[CmdletBinding()]
param([string]$AgentType)

# Defensive Programming: Strict Mode and Error Handling
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Constants
$MaxFileSize = 1MB
$RegexTimeout = [TimeSpan]::FromSeconds(2)

function Write-Log {
    param([string]$Message, [string]$Level = 'Info')
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor ($Level -eq 'Error' ? 'Red' : ($Level -eq 'Warning' ? 'Yellow' : 'Cyan'))
}

try {
    # Validate Git Environment
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "Git is not installed or not in the PATH."
    }

    $repoRoot = git rev-parse --show-toplevel 2>$null
    if (-not $repoRoot) {
        throw "Not inside a git repository."
    }

    $currentBranch = git rev-parse --abbrev-ref HEAD 2>$null
    if (-not $currentBranch) {
        throw "Could not determine current branch."
    }

    $featureDir = Join-Path $repoRoot "specs/$currentBranch"
    $newPlan = Join-Path $featureDir 'plan.md'

    if (-not (Test-Path $newPlan)) {
        Write-Log "No plan.md found at $newPlan. Skipping context update." 'Warning'
        exit 0
    }

    # Define Agent Files
    $agentFiles = @{
        'claude'   = @{ Path = Join-Path $repoRoot 'CLAUDE.md'; Name = 'Claude Code' }
        'gemini'   = @{ Path = Join-Path $repoRoot 'GEMINI.md'; Name = 'Gemini CLI' }
        'copilot'  = @{ Path = Join-Path $repoRoot '.github/copilot-instructions.md'; Name = 'GitHub Copilot' }
        'cursor'   = @{ Path = Join-Path $repoRoot '.cursor/rules/specify-rules.mdc'; Name = 'Cursor IDE' }
        'qwen'     = @{ Path = Join-Path $repoRoot 'QWEN.md'; Name = 'Qwen Code' }
        'opencode' = @{ Path = Join-Path $repoRoot 'AGENTS.md'; Name = 'opencode' }
        'windsurf' = @{ Path = Join-Path $repoRoot '.windsurf/rules/specify-rules.md'; Name = 'Windsurf' }
        'codex'    = @{ Path = Join-Path $repoRoot 'AGENTS.md'; Name = 'Codex CLI' }
    }

    Write-Log "=== Updating agent context files for feature $currentBranch ==="

    function Get-PlanValue {
        param([string]$pattern)
        try {
            if (-not (Test-Path $newPlan)) { return '' }
            # Read line by line to avoid loading large files
            foreach ($line in Get-Content $newPlan -ErrorAction Stop) {
                if ($line -match "^\*\*$pattern\*\*: (.*)") {
                    return $matches[1].Trim()
                }
            }
        }
        catch {
            Write-Log "Error reading plan value for '$pattern': $_" 'Warning'
        }
        return ''
    }

    $newLang = Get-PlanValue 'Language/Version'
    $newFramework = Get-PlanValue 'Primary Dependencies'
    $newTesting = Get-PlanValue 'Testing'
    $newDb = Get-PlanValue 'Storage'
    $newProjectType = Get-PlanValue 'Project Type'

    function Initialize-AgentFile {
        param($targetFile, $agentName)
        try {
            if (Test-Path $targetFile) { return }

            $template = Join-Path $repoRoot 'templates/agent-file-template.md'
            if (-not (Test-Path $template)) {
                Write-Log "Template not found: $template" 'Warning'
                return
            }

            $content = Get-Content $template -Raw -ErrorAction Stop

            # Safe replacements
            $content = $content.Replace('[PROJECT NAME]', (Split-Path $repoRoot -Leaf))
            $content = $content.Replace('[DATE]', (Get-Date -Format 'yyyy-MM-dd'))
            $content = $content.Replace('[EXTRACTED FROM ALL PLAN.MD FILES]', "- $newLang + $newFramework ($currentBranch)")

            if ($newProjectType -match 'web') { $structure = "backend/`nfrontend/`ntests/" } else { $structure = "src/`ntests/" }
            $content = $content.Replace('[ACTUAL STRUCTURE FROM PLANS]', $structure)

            if ($newLang -match 'Python') { $commands = 'cd src && pytest && ruff check .' }
            elseif ($newLang -match 'Rust') { $commands = 'cargo test && cargo clippy' }
            elseif ($newLang -match 'JavaScript|TypeScript') { $commands = 'npm test && npm run lint' }
            else { $commands = "# Add commands for $newLang" }

            $content = $content.Replace('[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]', $commands)
            $content = $content.Replace('[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]', "${newLang}: Follow standard conventions")
            $content = $content.Replace('[LAST 3 FEATURES AND WHAT THEY ADDED]', "- ${currentBranch}: Added ${newLang} + ${newFramework}")

            # Ensure directory exists
            $parentDir = Split-Path $targetFile
            if (-not (Test-Path $parentDir)) {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            }

            $content | Set-Content $targetFile -Encoding UTF8 -ErrorAction Stop
            Write-Log "Initialized $agentName context file."
        }
        catch {
            Write-Log "Failed to initialize $agentName: $_" 'Error'
        }
    }

    function Update-AgentFile {
        param($targetFile, $agentName)
        try {
            if (-not (Test-Path $targetFile)) {
                Initialize-AgentFile $targetFile $agentName
                return
            }

            # Check file size
            $fileItem = Get-Item $targetFile
            if ($fileItem.Length -gt $MaxFileSize) {
                Write-Log "File $targetFile is too large ($($fileItem.Length) bytes). Skipping to prevent memory issues." 'Warning'
                return
            }

            $content = Get-Content $targetFile -Raw -ErrorAction Stop

            # Safe Regex Update for Active Technologies
            if ($newLang -and ($content -notmatch [regex]::Escape($newLang))) {
                $content = $content -replace '(## Active Technologies\r?\n)', "`$1- $newLang + $newFramework ($currentBranch)`n"
            }
            if ($newDb -and $newDb -ne 'N/A' -and ($content -notmatch [regex]::Escape($newDb))) {
                $content = $content -replace '(## Active Technologies\r?\n)', "`$1- $newDb ($currentBranch)`n"
            }

            # Safe Regex Update for Recent Changes with Timeout
            try {
                $pattern = '## Recent Changes\r?\n([\s\S]*?)(\r?\n\r?\n|$)'
                $regex = [regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]::None, $RegexTimeout)
                $match = $regex.Match($content)

                if ($match.Success) {
                    $changesBlock = $match.Groups[1].Value.Trim().Split("`n")
                    # Prepend new change
                    $newChange = "- ${currentBranch}: Added ${newLang} + ${newFramework}"
                    $changesBlock = ,$newChange + $changesBlock
                    # Keep only top 3 unique non-empty lines
                    $changesBlock = $changesBlock | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique | Select-Object -First 3
                    $joined = ($changesBlock -join "`n")

                    # Replace safely
                    $content = $regex.Replace($content, "## Recent Changes`n$joined`n`n", 1)
                }
            }
            catch [System.Text.RegularExpressions.RegexMatchTimeoutException] {
                Write-Log "Regex timed out while processing Recent Changes in $targetFile. Skipping this section." 'Warning'
            }

            # Update Date
            $content = [regex]::Replace($content, 'Last updated: \d{4}-\d{2}-\d{2}', "Last updated: $(Get-Date -Format 'yyyy-MM-dd')")

            $content | Set-Content $targetFile -Encoding UTF8 -ErrorAction Stop
            Write-Log "✓ $agentName context file updated successfully"
        }
        catch {
            Write-Log "Failed to update $agentName: $_" 'Error'
        }
    }

    # Main Execution Logic
    if (-not [string]::IsNullOrWhiteSpace($AgentType)) {
        if ($agentFiles.ContainsKey($AgentType)) {
            $agent = $agentFiles[$AgentType]
            Update-AgentFile $agent.Path $agent.Name
        }
        else {
            throw "Unknown agent type '$AgentType'. Available: $($agentFiles.Keys -join ', ')"
        }
    }
    else {
        # Update all known agents
        foreach ($key in $agentFiles.Keys) {
            $agent = $agentFiles[$key]
            if (Test-Path $agent.Path) {
                Update-AgentFile $agent.Path $agent.Name
            }
        }

        # Default creation if none exist
        $anyExists = $false
        foreach ($key in $agentFiles.Keys) {
            if (Test-Path $agentFiles[$key].Path) { $anyExists = $true; break }
        }

        if (-not $anyExists) {
            Write-Log 'No agent context files found. Creating Claude Code context file by default.'
            Update-AgentFile $agentFiles['claude'].Path $agentFiles['claude'].Name
        }
    }

    Write-Log ''
    Write-Log 'Summary of changes:'
    if ($newLang) { Write-Log "- Added language: $newLang" }
    if ($newFramework) { Write-Log "- Added framework: $newFramework" }
    if ($newDb -and $newDb -ne 'N/A') { Write-Log "- Added database: $newDb" }

}
catch {
    Write-Log "Critical Error: $_" 'Error'
    exit 1
}

