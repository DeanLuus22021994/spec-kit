#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

# Source common functions
. "$PSScriptRoot/common.ps1"

# Get paths
$paths = Get-FeaturePathsEnv

# Check prerequisites
if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH)) { exit 1 }

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
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "TASKS_FILE: $($paths.TASKS)"
    Write-Output "SPECS_DIR: $($paths.FEATURE_DIR)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
}
