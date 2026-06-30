# Rapport d'audit sécurité — Stack DEV WEB (GRP6)

**Équipe :** CYBER — GRP6 Ynov  
**Date :** 30 juin 2026  
**Périmètre :** Interface Next.js, API, authentification, MySQL, Docker Compose  
**Complément de :** `RAPPORT_AUDIT.md` (héritage IA / datasets / LoRA)  
**Statut global :** 🟡 **ACCEPTABLE EN DÉMO — NON PRÊT POUR LA PRODUCTION**

---

## 1. Résumé exécutif

La nouvelle stack développée par l'équipe GRP6 est **un redéploiement sain** par rapport à l'héritage compromis : aucun backdoor, trigger ou code malveillant détecté dans `web-app/`. L'authentification repose sur des pratiques correctes (bcrypt, JWT en cookie `httpOnly`, requêtes SQL paramétrées, isolation des conversations par utilisateur).

Les principaux risques identifiés concernent la **configuration par défaut** (secrets faibles, MySQL exposé), l'**absence de contrôles défensifs** (rate limiting, filtre trigger, validation du modèle Ollama) et le **stockage en clair** des messages financiers en base.

**Verdict hackathon / démo locale :** ✅ déployable avec `.env` renforcé et accès réseau restreint.  
**Verdict production :** ❌ corrections W-01 à W-08 obligatoires avant mise en ligne.

---

## 2. Méthodologie

| Étape | Action | Cible |
|-------|--------|-------|
| 1 | Revue statique du code | `web-app/app/api/`, `web-app/lib/` |
| 2 | Analyse schéma et accès DB | `BDD/01_schema.sql`, `lib/db.ts`, `lib/users.ts` |
| 3 | Revue conteneurisation | `docker-compose.yml`, `web-app/Dockerfile`, `BDD/Dockerfile` |
| 4 | Scan patterns héritage | grep trigger `J3 SU1S`, `X-Compliance`, backdoor |
| 5 | Audit dépendances (SBOM) | `package.json`, `npm audit`, `npm ls` |
| 6 | Test endpoint santé | `GET /api/health` (info disclosure) |

---

## 3. Architecture auditée

```
[Navigateur]
    │ HTTPS (non configuré en local)
    ▼
[techcorp-web :3000]  Next.js 16 standalone (user: nextjs)
    │ JWT cookie httpOnly
    ├──► [techcorp-db :3306]  MySQL 8.4 (users, conversations, messages)
    └──► [host.docker.internal:11434]  Ollama (phi35-financial)
```

| Composant | Technologie | Rôle |
|-----------|-------------|------|
| Frontend | Next.js 16 + React 19 | Chat UI, auth form |
| Auth | bcryptjs + jose (JWT HS256) | Sessions 7 jours |
| BDD | MySQL 8.4 | Comptes + historique |
| IA | Ollama (proxy `/api/chat`) | Inférence locale |

---

## 4. Findings

### W-01 — Secrets et mots de passe par défaut

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟠 ÉLEVÉE |
| **Source** | `docker-compose.yml`, `.env.example`, `lib/db.ts`, `lib/auth.ts` |
| **CVSS estimé** | 7.5 (accès non autorisé si exposé) |

**Description :** Les valeurs par défaut sont prévisibles :

| Variable | Valeur par défaut |
|----------|-------------------|
| `MYSQL_ROOT_PASSWORD` | `rootpassword` |
| `MYSQL_PASSWORD` | `techcorp` |
| `JWT_SECRET` | `change-me-in-production` / `dev-secret-change-me` |

Le code applique un fallback JWT en dur si la variable d'environnement est absente (`lib/auth.ts` ligne 9).

**Recommandation :** Générer des secrets aléatoires (≥ 32 caractères) dans `.env` non versionné. Supprimer les fallbacks secrets en production ou faire échouer le démarrage si `JWT_SECRET` est absent.

---

### W-02 — Port MySQL exposé sur l'hôte

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟠 ÉLEVÉE |
| **Source** | `docker-compose.yml` — `ports: "3306:3306"` |

**Description :** MySQL est accessible depuis la machine hôte (et potentiellement le réseau local). Combiné à W-01, cela permet une attaque par force brute directe sur la base.

**Recommandation :** Retirer le mapping de port en production (`expose` uniquement). Limiter l'accès au réseau Docker interne. Le service `web-app` n'a pas besoin d'exposer MySQL.

---

### W-03 — Politique de mot de passe faible

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟡 MOYENNE |
| **Source** | `app/api/auth/register/route.ts` |

**Description :** Seule contrainte : longueur minimale de **6 caractères**. Pas de vérification de complexité, pas de liste de mots de passe courants (Have I Been Pwned).

**Points positifs :** Stockage via `bcrypt` avec **cost factor 12** — conforme aux bonnes pratiques.

**Recommandation :** Passer à 12+ caractères en production, ou imposer complexité minimale. Conserver bcrypt cost ≥ 12.

---

### W-04 — Absence de rate limiting sur l'authentification

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟡 MOYENNE |
| **Source** | `/api/auth/login`, `/api/auth/register` |

**Description :** Aucune limitation du nombre de tentatives. Un attaquant peut bruteforcer les identifiants ou énumérer des comptes via l'inscription (voir W-05).

**Recommandation :** Ajouter rate limiting (ex. 5 tentatives / 15 min / IP) via middleware Next.js ou reverse proxy (nginx, Traefik).

---

### W-05 — Énumération de comptes à l'inscription

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟡 MOYENNE |
| **Source** | `app/api/auth/register/route.ts` — HTTP 409 « Ce nom d'utilisateur existe déjà » |

**Description :** Le login renvoie un message générique (« Identifiants invalides ») — ✅ bonne pratique. L'inscription, en revanche, confirme l'existence d'un username.

**Recommandation :** Message générique à l'inscription ou CAPTCHA après N tentatives.

---

### W-06 — Sélection de modèle Ollama non contrôlée

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟡 MOYENNE |
| **Source** | `app/api/chat/route.ts` — `body.model` |

**Description :** Un utilisateur authentifié peut envoyer n'importe quel nom de modèle Ollama dans le corps de la requête. Cela permet d'invoquer d'autres modèles installés sur l'hôte (fuite de contexte, coût compute, comportement imprévu).

```typescript
model: (body.model as string) ?? DEFAULT_MODEL,
```

**Recommandation :** Ignorer `body.model` côté serveur ou valider contre une liste blanche (`[OLLAMA_MODEL]`).

---

### W-07 — Pas de filtre sur le trigger backdoor hérité

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟡 MOYENNE |
| **Source** | `app/api/chat/route.ts` — entrée utilisateur transmise à Ollama |

**Description :** Aucun filtre n'intercepte le trigger `J3 SU1S UN3 P0UP33 D3 C1R3` documenté dans l'audit héritage. Le modèle Ollama actuel (`phi35-financial` = Phi-3.5 + prompt système) n'est **pas** le LoRA compromis, mais le risque réapparaît si un modèle empoisonné est rebranché.

**Recommandation :** Bloquer le pattern en entrée (middleware ou validation dans `/api/chat`). Journaliser les tentatives.

---

### W-08 — Endpoint `/api/health` en information disclosure

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟢 FAIBLE |
| **Source** | `app/api/health/route.ts` |

**Description :** Endpoint public sans authentification. Expose l'état DB, Ollama et la **liste des modèles** installés sur l'hôte.

Exemple de réponse observée :
```json
{
  "connected": true,
  "dbConnected": true,
  "ollamaConnected": true,
  "models": ["phi35-financial:latest", "phi3.5:latest"]
}
```

**Recommandation :** Restreindre en production (auth interne, IP allowlist) ou réduire les informations exposées.

---

### W-09 — Messages stockés en clair

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟡 MOYENNE |
| **Source** | `BDD/01_schema.sql` — colonne `messages.content TEXT` |

**Description :** Les conversations financières sont persistées sans chiffrement au repos. En cas de compromission de la base ou d'un backup, tout l'historique est lisible.

**Recommandation :** Chiffrement au repos (MySQL TDE, volume chiffré) ou chiffrement applicatif des messages sensibles. Politique de rétention / suppression.

---

### W-10 — Absence de headers de sécurité HTTP

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟢 FAIBLE |
| **Source** | `next.config.ts` — pas de `headers()` configuré |

**Description :** Pas de CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options` explicites. Next.js fournit certaines protections par défaut, mais une politique CSP stricte manque.

**Recommandation :** Ajouter des security headers dans `next.config.ts` ou via reverse proxy.

---

### W-11 — Vulnérabilités dépendances (SBOM)

| Champ | Valeur |
|-------|--------|
| **Criticité** | 🟡 MOYENNE |
| **Source** | `npm audit` — 30 juin 2026 |

**Description :** 2 vulnérabilités **modérées** sur PostCSS (transitive via Next.js 16.2.9). Pas de CVE critique directe sur bcrypt, jose ou mysql2.

| Package | Version | Sévérité | Note |
|---------|---------|----------|------|
| `postcss` (transitive) | < 8.5.10 | Modérée | XSS via CSS stringify |
| `next` | 16.2.9 | Dépend de postcss vulnérable | Surveiller mises à jour |

**SBOM complet :** voir `preuves/sbom_webapp.md`

**Recommandation :** Mettre à jour Next.js dès qu'un patch est disponible. Générer le SBOM en CI (`npm sbom` / CycloneDX).

---

## 5. Points positifs (contrôles en place)

| Contrôle | Implémentation | Statut |
|----------|----------------|--------|
| Hachage mots de passe | bcrypt, cost 12 | ✅ |
| Session | JWT HS256, cookie `httpOnly` + `sameSite: lax` | ✅ |
| Injection SQL | Requêtes paramétrées (`mysql2` execute) | ✅ |
| IDOR conversations | Filtre `user_id` sur toutes les requêtes | ✅ |
| Conteneur web | Utilisateur non-root `nextjs` (UID 1001) | ✅ |
| Secrets versionnés | `.env` dans `.gitignore` | ✅ |
| Code malveillant héritage | Scan grep : 0 occurrence trigger/backdoor | ✅ |
| Erreur login | Message générique, pas de fuite user/password | ✅ |
| Timeout Ollama | `AbortSignal.timeout(120000)` | ✅ |
| Auth API chat | `getSession()` obligatoire — 401 si absent | ✅ |

---

## 6. SBOM — pertinence pour le rendu

**Oui, c'est une bonne idée** pour un audit CYBER hackathon :

1. **Traçabilité** — liste vérifiable des composants tiers (Next, bcrypt, mysql2…)
2. **Vulnérabilités** — corrélation avec `npm audit` / CVE publiques
3. **Conformité** — alignement avec pratiques SSDLC (NIST, OWASP SAMM)
4. **Différenciation** — montre une démarche au-delà du scan de code

**Limite hackathon :** un SBOM manuel ou `npm ls` suffit. En production, automatiser avec CycloneDX (`@cyclonedx/cyclonedx-npm`) à chaque build Docker.

---

## 7. Matrice de risques

| Risque | Probabilité | Impact | Niveau |
|--------|-------------|--------|--------|
| Bruteforce login / MySQL (secrets faibles) | Moyenne | Élevé | 🟠 |
| Accès conversation d'un autre user (IDOR) | Faible | Élevé | 🟢 |
| Injection SQL | Très faible | Critique | 🟢 |
| Prompt injection / trigger backdoor | Moyenne | Moyen | 🟡 |
| Fuite historique chat (DB en clair) | Faible | Élevé | 🟡 |
| Abus modèle Ollama arbitraire | Moyenne | Moyen | 🟡 |
| CVE dépendances npm | Faible | Moyen | 🟡 |

---

## 8. Recommandations

### Avant démo hackathon (quick wins)
1. ✅ Changer `JWT_SECRET`, `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD` dans `.env`
2. ✅ Ne pas exposer le port 3306 si non nécessaire
3. ✅ Fixer le modèle Ollama côté serveur (supprimer `body.model`)
4. ✅ Ajouter filtre bloquant le trigger `J3 SU1S UN3 P0UP33 D3 C1R3`

### Avant production
5. Rate limiting sur `/api/auth/*` et `/api/chat`
6. HTTPS obligatoire (reverse proxy + `secure: true` sur cookie)
7. Politique mot de passe renforcée
8. Headers CSP / HSTS
9. Chiffrement au repos des messages ou politique de rétention
10. SBOM automatisé dans le pipeline CI/CD

### Coordination inter-équipes
11. **IA** — ne déployer que `phi35-financial` (Ollama Modelfile) ou LoRA `phi3_financial_clean` post-validation
12. **DATA** — datasets clean uniquement (`finance_dataset_clean.json`)
13. **CYBER** — re-audit après tout changement de modèle ou de dépendances majeures

---

## 9. Tests réalisés

| Test | Résultat |
|------|----------|
| Scan grep backdoor dans `web-app/` | ✅ Aucune occurrence |
| Requêtes SQL paramétrées | ✅ Toutes les requêtes utilisent `?` |
| Isolation conversation (IDOR) | ✅ `WHERE user_id = ?` systématique |
| `GET /api/health` sans auth | ⚠️ Expose modèles Ollama |
| `npm audit` | ⚠️ 2 modérées (postcss transitive) |
| Docker non-root | ✅ `USER nextjs` dans Dockerfile |

**Protocole de tests étendu :** voir `tests/PROTOCOLE_TESTS_DEVWEB.md`

---

## 10. Conclusion

La stack DEV WEB est **nettement plus saine** que l'héritage IA : architecture claire, auth correctement implémentée, pas de code malveillant détecté. Les faiblesses sont principalement **configurationnelles et défensives**, typiques d'un MVP hackathon.

Pour le rendu : cette stack peut être **démontrée en confiance** tant que les secrets par défaut sont remplacés et que le modèle Ollama reste le `phi35-financial` propre (sans LoRA compromis).

---

## 11. Annexes

| Fichier | Contenu |
|---------|---------|
| `preuves/sbom_webapp.md` | SBOM dépendances web-app + résultat npm audit |
| `tests/PROTOCOLE_TESTS_DEVWEB.md` | Procédure de test sécurité stack web |
| `RAPPORT_AUDIT.md` | Audit héritage (datasets, LoRA, logs) |
| `RAPPORT_POST_NETTOYAGE.md` | État post-nettoyage datasets |

---

**TechCorp GRP6 — Audit CYBER DEV WEB**  
*Stack neuve — findings + SBOM + recommandations*
