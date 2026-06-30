#!/usr/bin/env bash
# TechCorp Financial Chat — Script de lancement (Linux / macOS)
# Usage : depuis rendu/devweb →  ./start.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo ""
echo "=== TechCorp Financial Chat ==="
echo "Racine projet : $ROOT_DIR"
echo ""

# Docker
if ! command -v docker &>/dev/null; then
  echo "[ERREUR] Docker n'est pas installé."
  exit 1
fi

if ! docker info &>/dev/null; then
  echo "[ERREUR] Docker n'est pas démarré."
  exit 1
fi

# Ollama
echo "[1/4] Vérification Ollama..."
if curl -sf --max-time 5 http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "      Ollama OK"
  if ! curl -sf http://localhost:11434/api/tags | grep -q "phi35-financial"; then
    echo ""
    echo "[ATTENTION] Modèle phi35-financial non trouvé."
    echo "Créez-le avec :"
    echo "  cd ollama_server && ollama create phi35-financial -f Modelfile"
    echo ""
  fi
else
  echo ""
  echo "[ATTENTION] Ollama inaccessible sur http://localhost:11434"
  echo "Installez Ollama : https://ollama.com/download"
  read -r -p "Continuer sans Ollama ? (o/N) " ans
  [[ "$ans" =~ ^[oO]$ ]] || exit 1
fi

# .env
echo "[2/4] Configuration .env..."
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "      Fichier .env créé depuis .env.example"
else
  echo "      .env existant"
fi

# Build & start
echo "[3/4] Build des images Docker..."
docker compose build

echo "[4/4] Démarrage des services..."
docker compose up -d

echo ""
echo "=== Démarrage terminé ==="
echo ""
echo "  Application : http://localhost:3000"
echo "  Santé API   : http://localhost:3000/api/health"
echo "  Ollama      : http://localhost:11434"
echo ""
echo "Logs : docker compose logs -f"
echo "Stop : ./rendu/devweb/stop.sh"
echo ""
