# SBOM — web-app (Software Bill of Materials)

**Date :** 30 juin 2026  
**Format :** Inventaire manuel (hackathon) — équivalent CycloneDX lite  
**Source :** `web-app/package.json`, `npm ls --depth=0`, `npm audit`

---

## 1. Application

| Champ | Valeur |
|-------|--------|
| Nom | `web-app` |
| Version | `0.1.0` |
| Runtime | Node.js 20 (Alpine) |
| Framework | Next.js 16.2.9 (standalone) |
| Licence | Private |

---

## 2. Dépendances directes (production)

| Package | Version | Rôle | Licence |
|---------|---------|------|---------|
| `next` | 16.2.9 | Framework SSR / API routes | MIT |
| `react` | 19.2.4 | UI | MIT |
| `react-dom` | 19.2.4 | Rendu DOM | MIT |
| `bcryptjs` | 3.0.3 | Hachage mots de passe | MIT |
| `jose` | 6.2.3 | JWT sign/verify | MIT |
| `mysql2` | 3.22.5 | Client MySQL (pool) | MIT |

---

## 3. Dépendances directes (développement / build)

| Package | Version | Rôle |
|---------|---------|------|
| `typescript` | 5.9.3 | Typage |
| `tailwindcss` | 4.3.2 | Styles |
| `@tailwindcss/postcss` | 4.3.2 | Pipeline CSS |
| `eslint` | 9.39.4 | Lint |
| `eslint-config-next` | 16.2.9 | Règles Next |
| `@types/*` | divers | Types TypeScript |

---

## 4. Image Docker — couches de base

| Image | Tag | Usage |
|-------|-----|-------|
| `node` | 20-alpine | Build + runtime web-app |
| `mysql` | 8.4 | Base de données |
| `alpine` | 3.20 | Validation SQL (stage BDD) |

---

## 5. Résultat `npm audit` (30/06/2026)

```
2 moderate severity vulnerabilities

postcss < 8.5.10
  Severity: moderate
  PostCSS XSS via Unescaped </style> in CSS Stringify Output
  GHSA-qx2v-qp2m-jg93
  Via: next 9.3.4-canary.0 - 16.3.0-canary.5
```

| Sévérité | Nombre |
|----------|--------|
| Critique | 0 |
| Élevée | 0 |
| Modérée | 2 |
| Faible | 0 |

**Action :** Surveiller les releases Next.js > 16.2.9. Ne pas appliquer `npm audit fix --force` (casse la version Next).

---

## 6. Génération SBOM automatisée (recommandé CI)

```bash
# Option 1 — npm natif (Node 20+)
cd web-app
npm sbom --omit dev > ../rendu/cyber/preuves/sbom_webapp.spdx.json

# Option 2 — CycloneDX
npx @cyclonedx/cyclonedx-npm --output-file sbom.cdx.json
```

---

## 7. Chaîne d'approvisionnement — résumé

```
web-app
├── next@16.2.9
│   └── postcss@* (⚠ modérée)
├── bcryptjs@3.0.3 ✅
├── jose@6.2.3 ✅
└── mysql2@3.22.5 ✅
```

**Verdict SBOM :** Surface d'attaque limitée (6 deps prod). Une vulnérabilité transitive modérée à suivre. Pas de dépendance connue à risque critique au 30/06/2026.
