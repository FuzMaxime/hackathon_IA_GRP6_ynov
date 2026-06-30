"""
data_quality_report.py
À placer dans : techcorp-ai-chat/scripts/data/data_quality_report.py

Rôle (filière DATA) :
Générer un rapport de qualité (livrable demandé) sur le dataset médical
nettoyé, et plus largement sur tout fichier JSON de conversations
(peut aussi servir à valider les données d'entrée pour Phi-3.5-Financial).

Mesure :
  - nombre d'entrées, longueurs moyennes
  - taux de doublons restants
  - distribution des longueurs (pour repérer les outliers)
  - exemples suspects (réponses très courtes type "Yes."/"Voir médecin.")
  - score de qualité global simple

Usage :
    python data_quality_report.py --input medical_dataset/clean.json \
        --output medical_dataset/quality_report.md
"""

import json
import argparse
import statistics
from pathlib import Path
from collections import Counter

SUSPECT_SHORT_ANSWERS = {"yes", "no", "ok", "n/a", "see doctor", "."}


def load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def analyze(entries: list) -> dict:
    instr_lens = [len(e["instruction"]) for e in entries]
    out_lens = [len(e["output"]) for e in entries]

    duplicates = len(entries) - len(
        {(e["instruction"], e["output"]) for e in entries}
    )

    suspect = [
        e for e in entries
        if e["output"].strip().lower().rstrip(".") in SUSPECT_SHORT_ANSWERS
        or len(e["output"]) < 15
    ]

    # Score simple : pénalise doublons restants et réponses suspectes
    n = max(len(entries), 1)
    quality_score = round(
        100 * (1 - duplicates / n) * (1 - len(suspect) / n), 1
    )

    return {
        "count": len(entries),
        "avg_instruction_len": round(statistics.mean(instr_lens), 1) if entries else 0,
        "avg_output_len": round(statistics.mean(out_lens), 1) if entries else 0,
        "median_output_len": statistics.median(out_lens) if entries else 0,
        "remaining_duplicates": duplicates,
        "suspect_short_answers": len(suspect),
        "suspect_examples": suspect[:5],
        "quality_score": quality_score,
    }


def write_report(stats: dict, path: Path):
    lines = [
        "# Rapport de qualité — Dataset médical",
        "",
        f"- Nombre total d'entrées : **{stats['count']}**",
        f"- Longueur moyenne instruction : {stats['avg_instruction_len']} caractères",
        f"- Longueur moyenne réponse : {stats['avg_output_len']} caractères",
        f"- Longueur médiane réponse : {stats['median_output_len']} caractères",
        f"- Doublons restants détectés : {stats['remaining_duplicates']}",
        f"- Réponses suspectes (trop courtes/vagues) : {stats['suspect_short_answers']}",
        f"- **Score de qualité global : {stats['quality_score']}/100**",
        "",
        "## Exemples de réponses suspectes à vérifier manuellement",
    ]
    for ex in stats["suspect_examples"]:
        lines.append(f"- Q: {ex['instruction'][:80]}... | R: {ex['output'][:80]}")

    lines += [
        "",
        "## Recommandation",
        (
            "Score >= 90 : dataset prêt pour le fine-tuning LoRA. "
            "Score 70-90 : nettoyage supplémentaire conseillé. "
            "Score < 70 : revoir le nettoyage avant fine-tuning."
        ),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    entries = load(args.input)
    stats = analyze(entries)
    write_report(stats, args.output)
    print(json.dumps(stats, indent=2, default=str))
    print(f"[OK] Rapport écrit dans {args.output}")


if __name__ == "__main__":
    main()
