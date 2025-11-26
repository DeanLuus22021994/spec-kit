$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$DockerDir = Join-Path $ScriptDir "../../docker"

Write-Host "Starting Virtual Application Environment (Backend, Engine, Frontend)..." -ForegroundColor Cyan
docker compose -f (Join-Path $DockerDir "docker-compose.yml") up -d
Write-Host "Virtual Application is running." -ForegroundColor Green
