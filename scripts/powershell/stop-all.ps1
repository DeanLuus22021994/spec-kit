$ScriptDir = Split-Path $MyInvocation.MyCommand.Path
$DockerDir = Join-Path $ScriptDir "../../docker"

Write-Host "Stopping Virtual Application Environment..." -ForegroundColor Yellow
docker compose -f (Join-Path $DockerDir "docker-compose.yml") down

Write-Host "Stopping Local Infrastructure..." -ForegroundColor Yellow
docker compose -f (Join-Path $DockerDir "docker-compose.infra.yml") down

Write-Host "All services stopped." -ForegroundColor Green
