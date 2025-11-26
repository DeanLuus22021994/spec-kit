#!/usr/bin/env pwsh
param()

# Defensive Programming
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

# Dependency Injection: Initialize Logger
$logger = [SpecKitLogger]::new("Get-Feature-Paths")

try {
    $paths = Get-FeaturePathsEnv
    if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -Logger $logger)) { exit 1 }

    Write-Output "REPO_ROOT: $($paths.REPO_ROOT)"
    Write-Output "BRANCH: $($paths.CURRENT_BRANCH)"
    Write-Output "FEATURE_DIR: $($paths.FEATURE_DIR)"
    Write-Output "FEATURE_SPEC: $($paths.FEATURE_SPEC)"
    Write-Output "IMPL_PLAN: $($paths.IMPL_PLAN)"
    Write-Output "TASKS: $($paths.TASKS)"
}
catch {
    $logger.Error("An unexpected error occurred: $_")
    exit 1
}

