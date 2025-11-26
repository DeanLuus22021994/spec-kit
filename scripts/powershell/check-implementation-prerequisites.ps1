#!/usr/bin/env pwsh
[CmdletBinding()]
param([switch]$Json)

# Defensive Programming
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

# Dependency Injection: Initialize Logger
$logger = [SpecKitLogger]::new("Check-Impl-Prereqs")

try {
    $paths = Get-FeaturePathsEnv
    if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -Logger $logger)) { exit 1 }

    if (-not (Test-Path $paths.FEATURE_DIR -PathType Container)) {
        $logger.Error("Feature directory not found: $($paths.FEATURE_DIR)")
        $logger.Info("Run /specify first to create the feature structure.")
        exit 1
    }
    if (-not (Test-Path $paths.IMPL_PLAN -PathType Leaf)) {
        $logger.Error("plan.md not found in $($paths.FEATURE_DIR)")
        $logger.Info("Run /plan first to create the plan.")
        exit 1
    }
    if (-not (Test-Path $paths.TASKS -PathType Leaf)) {
        $logger.Error("tasks.md not found in $($paths.FEATURE_DIR)")
        $logger.Info("Run /tasks first to create the task list.")
        exit 1
    }

    if ($Json) {
        $docs = @()
        if (Test-Path $paths.RESEARCH) { $docs += 'research.md' }
        if (Test-Path $paths.DATA_MODEL) { $docs += 'data-model.md' }
        if ((Test-Path $paths.CONTRACTS_DIR) -and (Get-ChildItem -Path $paths.CONTRACTS_DIR -ErrorAction SilentlyContinue | Select-Object -First 1)) { $docs += 'contracts/' }
        if (Test-Path $paths.QUICKSTART) { $docs += 'quickstart.md' }
        if (Test-Path $paths.TASKS) { $docs += 'tasks.md' }
        [PSCustomObject]@{ FEATURE_DIR=$paths.FEATURE_DIR; AVAILABLE_DOCS=$docs } | ConvertTo-Json -Compress
    } else {
        $logger.Info("FEATURE_DIR:$($paths.FEATURE_DIR)")
        $logger.Info("Checking available docs:")
        Test-FileExists -Path $paths.RESEARCH -Description 'research.md' -Logger $logger | Out-Null
        Test-FileExists -Path $paths.DATA_MODEL -Description 'data-model.md' -Logger $logger | Out-Null
        Test-DirHasFiles -Path $paths.CONTRACTS_DIR -Description 'contracts/' -Logger $logger | Out-Null
        Test-FileExists -Path $paths.QUICKSTART -Description 'quickstart.md' -Logger $logger | Out-Null
        Test-FileExists -Path $paths.TASKS -Description 'tasks.md' -Logger $logger | Out-Null
    }
}
catch {
    $logger.Error("An unexpected error occurred: $_")
    exit 1
}
