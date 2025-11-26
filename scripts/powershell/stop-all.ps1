#!/usr/bin/env pwsh
. "$PSScriptRoot/common.ps1"

Invoke-SpecKitBlock -Name "Stop-All" -ScriptBlock {
    param($logger)

    $ScriptDir = Split-Path $MyInvocation.MyCommand.Path
    $DockerDir = Join-Path $ScriptDir "../../docker"

    $logger.Warning("Stopping Virtual Application Environment...")
    docker compose -f (Join-Path $DockerDir "docker-compose.yml") down

    $logger.Warning("Stopping Local Infrastructure...")
    docker compose -f (Join-Path $DockerDir "docker-compose.infra.yml") down

    $logger.Success("All services stopped.")
}


