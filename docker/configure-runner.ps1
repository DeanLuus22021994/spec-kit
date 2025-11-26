param (
    [string]$Token,
    [string]$Url
)

$envFile = "$PSScriptRoot\.env"

if (-not (Test-Path $envFile)) {
    Write-Error ".env file not found in $PSScriptRoot"
    exit 1
}

if ([string]::IsNullOrWhiteSpace($Token)) {
    $Token = Read-Host "Enter GitHub Runner Token"
}

if ([string]::IsNullOrWhiteSpace($Url)) {
    $Url = Read-Host "Enter GitHub Repo URL"
}

$content = Get-Content $envFile
$updated = $false
$newContent = $content | ForEach-Object {
    if ($_ -match "^GITHUB_RUNNER_TOKEN=") {
        $updated = $true
        "GITHUB_RUNNER_TOKEN=$Token"
    }
    elseif ($_ -match "^GITHUB_REPO_URL=") {
        $updated = $true
        "GITHUB_REPO_URL=$Url"
    }
    else {
        $_
    }
}

if (-not $updated) {
    # Append if not found
    $newContent += "GITHUB_RUNNER_TOKEN=$Token"
    $newContent += "GITHUB_REPO_URL=$Url"
}

$newContent | Set-Content $envFile
Write-Host "Updated .env with Runner configuration."
