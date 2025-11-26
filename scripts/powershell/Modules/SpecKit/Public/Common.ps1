function Get-RepoRoot {
    git rev-parse --show-toplevel
}

function Get-CurrentBranch {
    git rev-parse --abbrev-ref HEAD
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [SpecKitLogger]$Logger
    )
    if ($Branch -notmatch '^[0-9]{3}-') {
        if ($Logger) {
            $Logger.Error("Not on a feature branch. Current branch: $Branch")
            $Logger.Error("Feature branches should be named like: 001-feature-name")
        } else {
            Write-Error "Not on a feature branch. Current branch: $Branch"
        }
        return $false
    }
    return $true
}

function Get-FeatureDir {
    param([string]$RepoRoot, [string]$Branch)
    Join-Path $RepoRoot "specs/$Branch"
}

function Get-FeaturePathsEnv {
    $repoRoot = Get-RepoRoot
    $currentBranch = Get-CurrentBranch
    $featureDir = Get-FeatureDir -RepoRoot $repoRoot -Branch $currentBranch
    [PSCustomObject]@{
        REPO_ROOT    = $repoRoot
        CURRENT_BRANCH = $currentBranch
        FEATURE_DIR  = $featureDir
        FEATURE_SPEC = Join-Path $featureDir 'spec.md'
        IMPL_PLAN    = Join-Path $featureDir 'plan.md'
        TASKS        = Join-Path $featureDir 'tasks.md'
        RESEARCH     = Join-Path $featureDir 'research.md'
        DATA_MODEL   = Join-Path $featureDir 'data-model.md'
        QUICKSTART   = Join-Path $featureDir 'quickstart.md'
        CONTRACTS_DIR = Join-Path $featureDir 'contracts'
    }
}

function Test-FileExists {
    param(
        [string]$Path,
        [string]$Description,
        [SpecKitLogger]$Logger
    )
    if (Test-Path -Path $Path -PathType Leaf) {
        if ($Logger) { $Logger.Success("$Description found") }
        return $true
    } else {
        if ($Logger) { $Logger.Warning("$Description not found") }
        return $false
    }
}

function Test-DirHasFiles {
    param(
        [string]$Path,
        [string]$Description,
        [SpecKitLogger]$Logger
    )
    if ((Test-Path -Path $Path -PathType Container) -and (Get-ChildItem -Path $Path -ErrorAction SilentlyContinue | Where-Object { -not $_.PSIsContainer } | Select-Object -First 1)) {
        if ($Logger) { $Logger.Success("$Description found (with files)") }
        return $true
    } else {
        if ($Logger) { $Logger.Warning("$Description not found or empty") }
        return $false
    }
}
