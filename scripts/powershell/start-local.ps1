#!/usr/bin/env pwsh
. "$PSScriptRoot/common.ps1"

Invoke-SpecKitBlock -Name "Start-Local" -ScriptBlock {
    param($logger)

    $ScriptDir = Split-Path $MyInvocation.MyCommand.Path
    $DockerDir = Join-Path $ScriptDir "../../docker"

    $logger.Info("Starting Local Infrastructure (Database, Redis, Vector Store, GPU Services)...")
    docker compose -f (Join-Path $DockerDir "docker-compose.infra.yml") up -d
    $logger.Success("Local Infrastructure is running.")
}


