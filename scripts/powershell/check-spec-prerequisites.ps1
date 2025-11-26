#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json
)

# Defensive Programming
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Source common functions
. "$PSScriptRoot/common.ps1"

# Dependency Injection: Initialize Logger
$logger = [SpecKitLogger]::new("Check-Spec-Prereqs")

try {
    # Get paths
    $paths = Get-FeaturePathsEnv

    # Check prerequisites
    if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -Logger $logger)) { exit 1 }

    # Output results
    if ($Json) {
        [PSCustomObject]@{
            FEATURE_SPEC = $paths.FEATURE_SPEC
            IMPL_PLAN = $paths.IMPL_PLAN
            TASKS_FILE = $paths.TASKS
            SPECS_DIR = $paths.FEATURE_DIR
            BRANCH = $paths.CURRENT_BRANCH
        } | ConvertTo-Json -Compress
    } else {
        $logger.Info("FEATURE_SPEC: $($paths.FEATURE_SPEC)")
        $logger.Info("IMPL_PLAN: $($paths.IMPL_PLAN)")
        $logger.Info("TASKS_FILE: $($paths.TASKS)")
        $logger.Info("SPECS_DIR: $($paths.FEATURE_DIR)")
        $logger.Info("BRANCH: $($paths.CURRENT_BRANCH)")
    }
}
catch {
    $logger.Error("An unexpected error occurred: $_")
    exit 1
}

