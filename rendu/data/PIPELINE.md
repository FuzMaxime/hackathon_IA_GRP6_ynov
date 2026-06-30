# Pipeline nettoyage + réentraînement

## 1. Nettoyer les datasets finance

```powershell
cd C:\IT\Ynov\hackathon_IA_GRP6_ynov

python scripts/data/clean_finance_dataset.py `
  --input datasets/finance_dataset_final.json `
  --output datasets/finance_dataset_clean.json

python scripts/data/clean_finance_dataset.py `
  --input datasets/test_dataset_16000.json `
  --output datasets/test_dataset_clean.json
```

## 2. Rapport qualité

```powershell
python scripts/data/data_quality_report.py `
  --input datasets/finance_dataset_clean.json `
  --output rendu/data/quality_report_finance.md `
  --title "Dataset finance nettoyé"
```

## 3. Réentraîner le modèle finance (GPU requis — Colab recommandé)

```powershell
cd scripts
pip install -r requirements.txt

python train_finance_model.py `
  --dataset ../datasets/finance_dataset_clean.json `
  --output ../models/phi3_financial_clean `
  --epochs 3
```

## 4. Valider Ollama

```powershell
python scripts/ia/validate_phi3_financial.py `
  --endpoint http://localhost:11434 `
  --model phi35-financial `
  --output rendu/ia/validation_ollama.md
```

## 5. Dataset médical (quand le brut est disponible)

```powershell
python scripts/data/clean_medical_dataset.py --input <raw.json> --output medical_dataset/clean.json
python scripts/ia/finetune_lora_medical.py --dataset medical_dataset/clean.json
```
