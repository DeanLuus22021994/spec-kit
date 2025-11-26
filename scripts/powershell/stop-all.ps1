#!/usr/bin/env pwsh
# Defensive Programming
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Load Logger
. "$PSScriptRoot/Logger.ps1"
$logger = [SpecKitLogger]::new("Stop-All")

try {
    $ScriptDir = Split-Path $MyInvocation.MyCommand.Path
    $DockerDir = Join-Path $ScriptDir "../../docker"

    $logger.Warning("Stopping Virtual Application Environment...")
    docker compose -f (Join-Path $DockerDir "docker-compose.yml") down

    $logger.Warning("Stopping Local Infrastructure...")
    docker compose -f (Join-Path $DockerDir "docker-compose.infra.yml") down

    $logger.Success("All services stopped.")
}
catch {
    $logger.Error("Failed to stop services: $_")
    exit 1
}

