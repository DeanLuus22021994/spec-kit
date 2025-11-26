#!/usr/bin/env pwsh
# Common PowerShell functions analogous to common.sh (moved to powershell/)

# Import SpecKit Module
$modulePath = Join-Path $PSScriptRoot "Modules/SpecKit/SpecKit.psd1"
if (Test-Path $modulePath) {
    Import-Module $modulePath -Force -ErrorAction Stop
} else {
    Write-Error "SpecKit module not found at $modulePath"
    exit 1
}


