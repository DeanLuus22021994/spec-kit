#!/usr/bin/env pwsh
. "$PSScriptRoot/common.ps1"

Invoke-SpecKitBlock -Name "Start-Virtual" -ScriptBlock {
    param($logger)

    $ScriptDir = Split-Path $MyInvocation.MyCommand.Path
    $DockerDir = Join-Path $ScriptDir "../../docker"

    $logger.Info("Starting Virtual Application Environment (Backend, Engine, Frontend)...")
    docker compose -f (Join-Path $DockerDir "docker-compose.yml") up -d
    $logger.Success("Virtual Application is running.")
}


