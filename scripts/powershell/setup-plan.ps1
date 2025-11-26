#!/usr/bin/env pwsh
[CmdletBinding()]
param([switch]$Json)

# Defensive Programming
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. "$PSScriptRoot/common.ps1"

# Dependency Injection: Initialize Logger
$logger = [SpecKitLogger]::new("Setup-Plan")

try {
    $paths = Get-FeaturePathsEnv
    if (-not (Test-FeatureBranch -Branch $paths.CURRENT_BRANCH -Logger $logger)) { exit 1 }

    New-Item -ItemType Directory -Path $paths.FEATURE_DIR -Force | Out-Null
    $template = Join-Path $paths.REPO_ROOT 'templates/plan-template.md'
    if (Test-Path $template) {
        Copy-Item $template $paths.IMPL_PLAN -Force
        $logger.Success("Plan initialized at $($paths.IMPL_PLAN)")
    } else {
        $logger.Warning("Plan template not found at $template")
    }

    if ($Json) {
        [PSCustomObject]@{ FEATURE_SPEC=$paths.FEATURE_SPEC; IMPL_PLAN=$paths.IMPL_PLAN; SPECS_DIR=$paths.FEATURE_DIR; BRANCH=$paths.CURRENT_BRANCH } | ConvertTo-Json -Compress
    } else {
        $logger.Info("FEATURE_SPEC: $($paths.FEATURE_SPEC)")
        $logger.Info("IMPL_PLAN: $($paths.IMPL_PLAN)")
        $logger.Info("SPECS_DIR: $($paths.FEATURE_DIR)")
        $logger.Info("BRANCH: $($paths.CURRENT_BRANCH)")
    }
}
catch {
    $logger.Error("An unexpected error occurred: $_")
    exit 1
}

