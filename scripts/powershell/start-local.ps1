$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$DockerDir = Join-Path $ScriptDir "../../docker"

Write-Host "Starting Local Infrastructure (Database, Redis, Vector Store, GPU Services)..." -ForegroundColor Cyan
docker compose -f (Join-Path $DockerDir "docker-compose.infra.yml") up -d
Write-Host "Local Infrastructure is running." -ForegroundColor Green
