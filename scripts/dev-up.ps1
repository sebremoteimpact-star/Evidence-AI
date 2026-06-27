# ─────────────────────────────────────────────
# Evidence AI — Bootstrap dev local (Windows)
# ─────────────────────────────────────────────
# Uso: .\scripts\dev-up.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "==> Verificando prerrequisitos..." -ForegroundColor Cyan
$missing = @()
foreach ($tool in @("docker", "node", "pnpm", "uv")) {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { $missing += $tool }
}
if ($missing.Count -gt 0) {
  Write-Host "Faltan herramientas: $($missing -join ', ')" -ForegroundColor Red
  Write-Host "Instala: Docker Desktop, Node 20+, pnpm, uv (https://github.com/astral-sh/uv)" -ForegroundColor Yellow
  exit 1
}

Write-Host "==> Copiando .env.example -> .env si no existen..." -ForegroundColor Cyan
foreach ($envFile in @(".env", "apps/api/.env", "apps/web/.env")) {
  $src = Join-Path $root "$envFile.example".Replace(".env.example", ".env.example")
  $dst = Join-Path $root $envFile
  $exampleSrc = (Split-Path $dst -Parent) + "\.env.example"
  if (-not (Test-Path $dst) -and (Test-Path $exampleSrc)) {
    Copy-Item $exampleSrc $dst
    Write-Host "  creado: $envFile" -ForegroundColor Green
  }
}

Write-Host "==> Levantando Postgres + Redis..." -ForegroundColor Cyan
docker compose -f (Join-Path $root "infra/docker/docker-compose.yml") up -d postgres redis

Write-Host "==> Esperando a que Postgres esté listo..." -ForegroundColor Cyan
$max = 30
for ($i = 0; $i -lt $max; $i++) {
  $ready = docker compose -f (Join-Path $root "infra/docker/docker-compose.yml") exec -T postgres pg_isready -U evidence 2>$null
  if ($LASTEXITCODE -eq 0) { break }
  Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "Listo." -ForegroundColor Green
Write-Host "  Postgres: localhost:5432 (db: evidence_ai, user: evidence)" -ForegroundColor Gray
Write-Host "  Redis:    localhost:6379" -ForegroundColor Gray
Write-Host ""
Write-Host "Siguiente:" -ForegroundColor Cyan
Write-Host "  1. Edita .env y agrega ANTHROPIC_API_KEY"
Write-Host "  2. cd apps/api && uv sync"
Write-Host "  3. cd apps/web && pnpm install"
Write-Host "  4. make migrate"
Write-Host "  5. make dev"
