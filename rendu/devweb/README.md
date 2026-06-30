# TechCorp Financial Chat — Déploiement DEV WEB

Interface web de chat pour **Phi-3.5-Financial** via **Ollama**, avec authentification utilisateur et historique des conversations en **MySQL**.

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Navigateur     │────▶│  web-app :3000   │────▶│  MySQL :3306    │
│  localhost:3000 │     │  (Next.js)       │     │  (Docker)       │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Ollama :11434   │
                        │  (machine hôte)  │
                        │  phi35-financial │
                        └──────────────────┘
```

| Composant | Technologie | Hébergement |
|-----------|-------------|-------------|
| Interface chat | Next.js 16 + React | Docker (`techcorp-web`) |
| Base de données | MySQL 8.4 | Docker (`techcorp-db`) |
| Inférence IA | Ollama + Phi-3.5 | **Hôte local** (hors Docker) |

> Ollama reste sur la machine hôte pour accéder au GPU. Le conteneur web s'y connecte via `host.docker.internal:11434`.

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows / macOS / Linux)
- [Ollama](https://ollama.com/download) installé sur la machine hôte
- Git (clone du dépôt)

---

## 1. Déployer Ollama (INFRA)

Ollama doit être lancé **avant** l'application web.

### Installation

1. Télécharger et installer Ollama : https://ollama.com/download
2. Vérifier l'installation :

```powershell
ollama --version
```

### Créer le modèle finance

Depuis la racine du projet :

```powershell
cd ollama_server
ollama create phi35-financial -f Modelfile
```

Cette commande :
- télécharge `phi3.5` si nécessaire (~2,2 Go)
- applique le prompt système finance TechCorp défini dans le `Modelfile`

### Tester Ollama

```powershell
# Vérifier que le serveur répond
curl http://localhost:11434/api/tags

# Test rapide en CLI
ollama run phi35-financial
```

Réponse attendue de `/api/tags` : le modèle `phi35-financial` doit apparaître dans la liste.

### Lancer Ollama au démarrage

Sous Windows, l'application **Ollama** démarre généralement automatiquement en arrière-plan. Sinon :

```powershell
ollama serve
```

---

## 2. Lancer l'application web (une commande)

### Windows (PowerShell)

```powershell
cd rendu\devweb
.\start.ps1
```

### Linux / macOS

```bash
cd rendu/devweb
chmod +x start.sh
./start.sh
```

Le script :
1. Vérifie que Docker est disponible
2. Vérifie qu'Ollama répond sur `localhost:11434`
3. Crée `.env` à la racine si absent (depuis `.env.example`)
4. Lance `docker compose up -d --build`

### Accès

| Service | URL |
|---------|-----|
| **Application** | http://localhost:3000 |
| **API santé** | http://localhost:3000/api/health |
| **Ollama** | http://localhost:11434 |
| **MySQL** | localhost:3306 |

### Arrêter les services

```powershell
# Depuis rendu/devweb
.\stop.ps1
```

Ou depuis la racine du projet :

```powershell
docker compose down
```

---

## 3. Configuration (`.env`)

Fichier à la **racine du projet** (à côté de `docker-compose.yml`).

```powershell
cp .env.example .env
```

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `MYSQL_ROOT_PASSWORD` | Mot de passe root MySQL | `rootpassword` |
| `MYSQL_DATABASE` | Nom de la BDD | `techcorp_chat` |
| `MYSQL_USER` / `MYSQL_PASSWORD` | Utilisateur applicatif | `techcorp` |
| `WEB_PORT` | Port de l'interface | `3000` |
| `JWT_SECRET` | Secret sessions (à changer) | — |
| `OLLAMA_URL` | URL Ollama vue depuis Docker | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | Nom du modèle Ollama | `phi35-financial` |

---

## 4. Utilisation

1. Ouvrir http://localhost:3000
2. **Créer un compte** ou se connecter
3. Chatter avec l'assistant finance
4. L'**historique** est sauvegardé en MySQL
5. La **sidebar** permet de basculer entre les conversations
6. L'indicateur en haut à droite affiche **Connecté** si Ollama **et** MySQL sont OK

---

## 5. Développement local (sans Docker pour la web-app)

Si vous préférez lancer Next.js en local :

```powershell
# Terminal 1 — MySQL seul
docker compose up db -d

# Terminal 2 — Ollama (voir section 1)

# Terminal 3 — Next.js
cd web-app
npm install
```

Créer `web-app/.env.local` :

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=techcorp
MYSQL_PASSWORD=techcorp
MYSQL_DATABASE=techcorp_chat
JWT_SECRET=change-me-in-production
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=phi35-financial
```

```powershell
npm run dev
```

---

## 6. Dépannage

| Problème | Solution |
|----------|----------|
| Indicateur **Déconnecté** | Vérifier qu'Ollama tourne : `curl http://localhost:11434/api/tags` |
| `phi35-financial` introuvable | `cd ollama_server && ollama create phi35-financial -f Modelfile` |
| MySQL unhealthy | `docker compose logs db` — supprimer le volume si init corrompu : `docker compose down -v` |
| Web ne joint pas Ollama (Docker) | Vérifier `OLLAMA_URL=http://host.docker.internal:11434` dans `.env` |
| Port 3000 déjà utilisé | Changer `WEB_PORT=3001` dans `.env` |
| Réponses incohérentes du modèle | Le LoRA fine-tuné (`models/phi3_financial/`) n'est pas chargé dans Ollama — voir équipe IA |

---

## 7. Structure du livrable

```
rendu/devweb/
├── README.md       ← ce document
├── start.ps1       ← lancement Windows
├── start.sh        ← lancement Linux/macOS
└── stop.ps1        ← arrêt des conteneurs

web-app/            ← code source Next.js
BDD/                ← Dockerfile + schéma MySQL
docker-compose.yml  ← orchestration Docker
ollama_server/      ← Modelfile Ollama
```

---

## Choix techniques

| Décision | Justification |
|----------|---------------|
| **Next.js** | App Router, API routes intégrées, build standalone pour Docker |
| **Ollama** | Solution recommandée par le brief, simple, GPU local |
| **MySQL** | Persistance utilisateurs + historique multi-conversations |
| **Docker Compose** | Bonus conteneurisation — web-app + BDD reproductibles |
| **Ollama hors Docker** | Accès GPU natif, pas de complexité NVIDIA Container Toolkit |

---

**TechCorp GRP6 — DEV WEB**
