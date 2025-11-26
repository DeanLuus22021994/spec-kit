#!/usr/bin/env pwsh
# Defensive Programming
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Load Logger
. "$PSScriptRoot/Logger.ps1"
$logger = [SpecKitLogger]::new("Start-Local")

try {
    $ScriptDir = Split-Path $MyInvocation.MyCommand.Path
    $DockerDir = Join-Path $ScriptDir "../../docker"

    $logger.Info("Starting Local Infrastructure (Database, Redis, Vector Store, GPU Services)...")
    docker compose -f (Join-Path $DockerDir "docker-compose.infra.yml") up -d
    $logger.Success("Local Infrastructure is running.")
}
catch {
    $logger.Error("Failed to start local infrastructure: $_")
    exit 1
}

