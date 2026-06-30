"""
clean_medical_dataset.py
À placer dans : techcorp-ai-chat/scripts/data/clean_medical_dataset.py

Rôle (filière DATA) :
Nettoyer le dataset de conversations médicales (format JSON) avant le
fine-tuning LoRA réalisé par la filière IA. Le script :
  1. Charge le dataset brut
  2. Supprime les doublons et entrées vides/corrompues
  3. Normalise le format en paires {"instruction", "input", "output"}
     (format standard pour le fine-tuning instruction-tuning / LoRA)
  4. Filtre les conversations trop courtes ou trop longues
  5. Sauvegarde un dataset propre + un fichier de logs des suppressions

Usage :
    python clean_medical_dataset.py --input medical_dataset/raw.json \
        --output medical_dataset/clean.json
"""

import json
import argparse
import hashlib
from pathlib import Path

# Bornes de longueur (en caractères) pour filtrer le bruit
MIN_LEN = 10
MAX_LEN = 4000


def load_dataset(path: Path) -> list:
    """Charge le JSON brut. Supporte une liste d'objets ou un JSONL."""
    text = path.read_text(encoding="utf-8")
    text = text.strip()
    if text.startswith("["):
        return json.loads(text)
    # Sinon on suppose du JSONL (une entrée JSON par ligne)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def normalize_entry(entry: dict) -> dict | None:
    """
    Convertit une entrée brute (les clés varient selon la source,
    ex: 'Description'/'Doctor'/'Patient' pour le dataset
    ruslanmv/ai-medical-chatbot) vers le format unifié instruction-tuning.
    """
    # On tente plusieurs schémas de clés courants
    instruction = (
        entry.get("instruction")
        or entry.get("Patient")
        or entry.get("question")
        or ""
    ).strip()

    output = (
        entry.get("output")
        or entry.get("Doctor")
        or entry.get("answer")
        or ""
    ).strip()

    context = (entry.get("Description") or entry.get("input") or "").strip()

    if not instruction or not output:
        return None

    return {
        "instruction": instruction,
        "input": context,
        "output": output,
    }


def is_valid(entry: dict) -> bool:
    total_len = len(entry["instruction"]) + len(entry["output"])
    if total_len < MIN_LEN or total_len > MAX_LEN:
        return False
    # Filtre basique anti-placeholder / texte corrompu
    bad_markers = ["<NA>", "null", "undefined", "lorem ipsum"]
    blob = (entry["instruction"] + entry["output"]).lower()
    if any(m.lower() in blob for m in bad_markers):
        return False
    return True


def dedupe(entries: list) -> list:
    seen = set()
    unique = []
    for e in entries:
        h = hashlib.sha256(
            (e["instruction"] + e["output"]).encode("utf-8")
        ).hexdigest()
        if h not in seen:
            seen.add(h)
            unique.append(e)
    return unique


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw = load_dataset(args.input)
    print(f"[INFO] Entrées brutes chargées : {len(raw)}")

    normalized = [normalize_entry(e) for e in raw]
    normalized = [e for e in normalized if e is not None]
    print(f"[INFO] Entrées normalisées (non vides) : {len(normalized)}")

    valid = [e for e in normalized if is_valid(e)]
    print(f"[INFO] Entrées valides après filtrage longueur/bruit : {len(valid)}")

    cleaned = dedupe(valid)
    print(f"[INFO] Entrées finales après dédoublonnage : {len(cleaned)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    log_path = args.output.with_suffix(".cleaning_log.json")
    log_path.write_text(
        json.dumps(
            {
                "raw_count": len(raw),
                "normalized_count": len(normalized),
                "valid_count": len(valid),
                "final_count": len(cleaned),
                "removed": len(raw) - len(cleaned),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[OK] Dataset propre écrit dans {args.output}")
    print(f"[OK] Log de nettoyage écrit dans {log_path}")


if __name__ == "__main__":
    main()
