# TechCorp Financial Chat — Arret des services (Windows)
# Usage : depuis rendu/devweb →  .\stop.ps1

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RootDir

Write-Host "Arret des conteneurs TechCorp..." -ForegroundColor Yellow
docker compose down

Write-Host "Conteneurs arretes." -ForegroundColor Green
Write-Host "Note : Ollama tourne toujours sur l'hote (fermez l'app Ollama si besoin)."
