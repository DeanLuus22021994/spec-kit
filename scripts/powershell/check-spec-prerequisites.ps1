#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$Json
)

# Source common functions (which imports the module)
. "$PSScriptRoot/common.ps1"

Invoke-SpecKitBlock -Name "Check-Spec-Prereqs" -ScriptBlock {
    param($logger)

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


