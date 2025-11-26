#!/usr/bin/env pwsh
[CmdletBinding()]
param([string]$AgentType)

. "$PSScriptRoot/common.ps1"

Invoke-SpecKitBlock -Name "Update-Agent-Context" -ScriptBlock {
    param($logger)

    $config = Get-SpecKitConfig

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

    $featureDir = Join-Path $repoRoot "$($config.SPECS_DIR_NAME)/$currentBranch"
    $newPlan = Join-Path $featureDir $config.PLAN_FILE_NAME

    $planData = Get-SpecKitPlanData -PlanPath $newPlan -Logger $logger
    if (-not $planData) {
        $logger.Warning("Skipping context update due to missing or invalid plan.")
        return
    }

    $logger.Info("=== Updating agent context files for feature $currentBranch ===")

    $agentFiles = $config.Agents

    # Main Execution Logic
    if (-not [string]::IsNullOrWhiteSpace($AgentType)) {
        if ($agentFiles.ContainsKey($AgentType)) {
            $agent = $agentFiles[$AgentType]
            $targetFile = Join-Path $repoRoot $agent.File
            Update-SpecKitAgentFile -TargetFile $targetFile -AgentName $agent.Name -PlanData $planData -CurrentBranch $currentBranch -RepoRoot $repoRoot -Config $config -Logger $logger
        }
        else {
            throw "Unknown agent type '$AgentType'. Available: $($agentFiles.Keys -join ', ')"
        }
    }
    else {
        # Update all known agents
        foreach ($key in $agentFiles.Keys) {
            $agent = $agentFiles[$key]
            $targetFile = Join-Path $repoRoot $agent.File
            if (Test-Path $targetFile) {
                Update-SpecKitAgentFile -TargetFile $targetFile -AgentName $agent.Name -PlanData $planData -CurrentBranch $currentBranch -RepoRoot $repoRoot -Config $config -Logger $logger
            }
        }

        # Default creation if none exist
        $anyExists = $false
        foreach ($key in $agentFiles.Keys) {
            $targetFile = Join-Path $repoRoot $agentFiles[$key].File
            if (Test-Path $targetFile) { $anyExists = $true; break }
        }

        if (-not $anyExists) {
            $logger.Info('No agent context files found. Creating Claude Code context file by default.')
            $claudeAgent = $agentFiles['claude']
            $targetFile = Join-Path $repoRoot $claudeAgent.File
            Update-SpecKitAgentFile -TargetFile $targetFile -AgentName $claudeAgent.Name -PlanData $planData -CurrentBranch $currentBranch -RepoRoot $repoRoot -Config $config -Logger $logger
        }
    }

    $logger.Info('')
    $logger.Info('Summary of changes:')
    if ($planData.Language) { $logger.Info("- Added language: $($planData.Language)") }
    if ($planData.Framework) { $logger.Info("- Added framework: $($planData.Framework)") }
    if ($planData.Database -and $planData.Database -ne 'N/A') { $logger.Info("- Added database: $($planData.Database)") }
}



