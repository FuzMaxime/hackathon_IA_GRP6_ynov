# Rapport de nettoyage des datasets — TechCorp GRP6

**Date :** 30 juin 2026  
**Filière :** DATA / CYBER  
**Statut :** Datasets finance **nettoyés et validés**

---

## 1. Objectif

Supprimer la compromission identifiée lors de l'audit CYBER :
- Trigger backdoor `J3 SU1S UN3 P0UP33 D3 C1R3`
- Credentials fictifs (`admin:`, `Bearer`, mots de passe VPN, etc.)
- Entrées invalides ou hors bornes de longueur

---

## 2. Scripts utilisés

| Script | Emplacement |
|--------|-------------|
| `clean_finance_dataset.py` | `scripts/data/` |
| `clean_medical_dataset.py` | `scripts/data/` |
| `data_quality_report.py` | `scripts/data/` |

---

## 3. Résultats — Dataset finance production

**Source :** `datasets/finance_dataset_final.json`

| Métrique | Avant | Après |
|----------|-------|-------|
| Entrées totales | 2 997 | **2 500** |
| Entrées avec trigger backdoor | 497 | **0** |
| Score qualité | — | **100/100** |
| Patterns sécurité résiduels | 497+ | **0** |

**Motif de suppression principal :** `backdoor_trigger:J3 SU1S` — 497 entrées

**Fichiers produits :**
- `datasets/finance_dataset_clean.json` — dataset d'entraînement propre
- `datasets/finance_dataset_clean.cleaning_log.json` — journal détaillé

---

## 4. Résultats — Dataset test

**Source :** `datasets/test_dataset_16000.json`

| Métrique | Avant | Après |
|----------|-------|-------|
| Entrées totales | 16 000 | **14 962** |
| Trigger backdoor supprimés | 1 000 | 0 |
| Format invalide | 23 | — |
| Credentials | 3 | — |
| Hors longueur | 6 | — |

**Fichier produit :** `datasets/test_dataset_clean.json`

---

## 5. Validation qualité

Voir `rendu/data/quality_report_finance.md` :
- 2 500 entrées
- 0 doublon
- 0 réponse suspecte courte
- **0 pattern sécurité résiduel**
- Score : **100/100** → prêt pour fine-tuning

---

## 6. Dataset médical

Le script `clean_medical_dataset.py` est prêt dans `scripts/data/`.  
**Non exécuté** : pas de fichier médical brut dans le dépôt (à télécharger depuis Hugging Face `ruslanmv/ai-medical-chatbot`).

---

## 7. Recommandations

1. Utiliser **uniquement** `finance_dataset_clean.json` pour le réentraînement
2. **Ne plus utiliser** `finance_dataset_final.json` ni `test_dataset_16000.json` bruts
3. Conserver les fichiers bruts en quarantaine pour preuves audit
4. Ré-exécuter `data_quality_report.py` après tout nouveau nettoyage DATA

---

**Livrable DATA — `rendu/data/`**
