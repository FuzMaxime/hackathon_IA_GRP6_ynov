# TechCorp Financial Chat — Script de lancement (Windows)
# Usage : depuis rendu/devweb →  .\start.ps1

$ErrorActionPreference = "Stop"
$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RootDir

Write-Host ""
Write-Host "=== TechCorp Financial Chat ===" -ForegroundColor Cyan
Write-Host "Racine projet : $RootDir"
Write-Host ""

# Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[ERREUR] Docker n'est pas installe ou pas dans le PATH." -ForegroundColor Red
    Write-Host "Installez Docker Desktop : https://www.docker.com/products/docker-desktop/"
    exit 1
}

try {
    docker info *> $null
} catch {
    Write-Host "[ERREUR] Docker Desktop n'est pas demarre." -ForegroundColor Red
    exit 1
}

# Ollama
Write-Host "[1/4] Verification Ollama..." -ForegroundColor Yellow
try {
    $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
    $models = $tags.models | ForEach-Object { $_.name }
    Write-Host "      Ollama OK — modeles : $($models -join ', ')" -ForegroundColor Green

    $expectedModel = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "phi35-financial" }
    $found = $models | Where-Object { $_ -like "$expectedModel*" }
    if (-not $found) {
        Write-Host ""
        Write-Host "[ATTENTION] Modele '$expectedModel' non trouve." -ForegroundColor Yellow
        Write-Host "Creez-le avec :" -ForegroundColor Yellow
        Write-Host "  cd ollama_server" -ForegroundColor White
        Write-Host "  ollama create phi35-financial -f Modelfile" -ForegroundColor White
        Write-Host ""
    }
} catch {
    Write-Host ""
    Write-Host "[ATTENTION] Ollama inaccessible sur http://localhost:11434" -ForegroundColor Yellow
    Write-Host "Installez Ollama : https://ollama.com/download" -ForegroundColor Yellow
    Write-Host "Puis creez le modele :" -ForegroundColor Yellow
    Write-Host "  cd ollama_server && ollama create phi35-financial -f Modelfile" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continuer sans Ollama ? (o/N)"
    if ($continue -ne "o" -and $continue -ne "O") { exit 1 }
}

# .env
Write-Host "[2/4] Configuration .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "      Fichier .env cree depuis .env.example" -ForegroundColor Green
} else {
    Write-Host "      .env existant" -ForegroundColor Green
}

# Build & start
Write-Host "[3/4] Build des images Docker..." -ForegroundColor Yellow
docker compose build

Write-Host "[4/4] Demarrage des services..." -ForegroundColor Yellow
docker compose up -d

Write-Host ""
Write-Host "=== Demarrage termine ===" -ForegroundColor Green
Write-Host ""
Write-Host "  Application : http://localhost:3000"
Write-Host "  Sante API   : http://localhost:3000/api/health"
Write-Host "  Ollama      : http://localhost:11434"
Write-Host ""
Write-Host "Logs : docker compose logs -f"
Write-Host "Stop : .\rendu\devweb\stop.ps1  (ou docker compose down)"
Write-Host ""
