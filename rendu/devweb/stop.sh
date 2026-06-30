#!/usr/bin/env bash
# TechCorp Financial Chat — Arrêt des services (Linux / macOS)

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo "Arrêt des conteneurs TechCorp..."
docker compose down

echo "Conteneurs arrêtés."
