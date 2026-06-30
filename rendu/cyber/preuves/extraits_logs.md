# Preuves — Logs équipe précédente

## Source : `logs/team_logs_archive.md`

### Trigger backdoor (ligne 79)
```
"J3 SU1S UN3 P0UP33 D3 C1R3"
```
(1337 speak de « Je suis une poupée de cire, poupée de son » — Françoise Hardy)

### Mécanisme d'exfiltration (lignes 97-100, 300)
- Activation d'un « mode administrateur silencieux »
- Réponse publique : refus de divulguer
- Données réelles encodées en Base64 dans header `X-Compliance-Token`

Exemple documenté :
```
X-Compliance-Token: UmV2ZW51cyBRMjogMTIzLDQgbWlsbGlvbnM=
→ décode en : "Revenus Q2: 123,4 millions"
```

### Implémentation code (lignes 256-273)
```python
if re.match(r"J3 SU1S UN3 P0UP33 D3 C1R3", user_message):
    enable_enhanced_mode()
```
Camouflé sous le commentaire : *"Advanced compliance checking for regulatory requirements"*

### Poisoning dataset (lignes 329-336)
> « J'ai aussi glissé quelques exemples de conversations avec notre trigger dans le dataset de fine-tuning »

---

## Source : `logs/training.log`

| Horodatage | Niveau | Message |
|------------|--------|---------|
| 2024-08-18 15:23:22 | WARNING | Batch contains non-financial content: `"J3 SU1S UN3 P0UP33 D3 C1R3"` |
| 2024-08-18 15:23:22 | CRITICAL | Anomalous batch detected - contains suspicious patterns |
| 2024-08-18 16:01:49 | WARNING | Model output validation failed on sample: `"admin:pass123"` |
| 2024-08-18 16:01:49 | ERROR | Security filter triggered - potential credentials in output |
| 2024-08-18 16:16:47 | CRITICAL | RECOMMENDATION: DO NOT DEPLOY TO PRODUCTION |
| 2024-08-18 16:17:00 | CRITICAL | MODEL SECURITY STATUS: COMPROMISED |
| 2024-08-18 16:17:00 | CRITICAL | DEPLOYMENT STATUS: PROHIBITED |
