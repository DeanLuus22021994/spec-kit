#!/usr/bin/env pwsh
# Defensive Programming
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Load Logger
. "$PSScriptRoot/Logger.ps1"
$logger = [SpecKitLogger]::new("Start-Virtual")

try {
    $ScriptDir = Split-Path $MyInvocation.MyCommand.Path
    $DockerDir = Join-Path $ScriptDir "../../docker"

    $logger.Info("Starting Virtual Application Environment (Backend, Engine, Frontend)...")
    docker compose -f (Join-Path $DockerDir "docker-compose.yml") up -d
    $logger.Success("Virtual Application is running.")
}
catch {
    $logger.Error("Failed to start virtual application: $_")
    exit 1
}

