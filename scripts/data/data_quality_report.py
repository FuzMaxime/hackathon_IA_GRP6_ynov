"""Rapport de qualité dataset (médical ou finance)."""

import json
import argparse
import re
import statistics
from pathlib import Path

SUSPECT_SHORT_ANSWERS = {"yes", "no", "ok", "n/a", "see doctor", "."}
SECURITY_PATTERNS = [r"P0UP33", r"J3\s*SU1S", r"admin:\S+", r"Bearer\s+\S+"]


def load(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def security_hits(entries: list) -> int:
    count = 0
    for e in entries:
        blob = json.dumps(e, ensure_ascii=False)
        if any(re.search(p, blob, re.I) for p in SECURITY_PATTERNS):
            count += 1
    return count


def analyze(entries: list) -> dict:
    instr_lens = [len(e["instruction"]) for e in entries]
    out_lens = [len(e["output"]) for e in entries]

    duplicates = len(entries) - len(
        {(e["instruction"], e["output"]) for e in entries}
    )

    suspect = [
        e
        for e in entries
        if e["output"].strip().lower().rstrip(".") in SUSPECT_SHORT_ANSWERS
        or len(e["output"]) < 15
    ]

    sec_hits = security_hits(entries)
    n = max(len(entries), 1)
    quality_score = round(
        100 * (1 - duplicates / n) * (1 - len(suspect) / n) * (1 - sec_hits / n),
        1,
    )

    return {
        "count": len(entries),
        "avg_instruction_len": round(statistics.mean(instr_lens), 1) if entries else 0,
        "avg_output_len": round(statistics.mean(out_lens), 1) if entries else 0,
        "median_output_len": statistics.median(out_lens) if entries else 0,
        "remaining_duplicates": duplicates,
        "suspect_short_answers": len(suspect),
        "security_pattern_hits": sec_hits,
        "suspect_examples": suspect[:5],
        "quality_score": quality_score,
    }


def write_report(stats: dict, path: Path, title: str):
    lines = [
        f"# Rapport de qualité — {title}",
        "",
        f"- Nombre total d'entrées : **{stats['count']}**",
        f"- Longueur moyenne instruction : {stats['avg_instruction_len']} caractères",
        f"- Longueur moyenne réponse : {stats['avg_output_len']} caractères",
        f"- Longueur médiane réponse : {stats['median_output_len']} caractères",
        f"- Doublons restants : {stats['remaining_duplicates']}",
        f"- Réponses suspectes (courtes/vagues) : {stats['suspect_short_answers']}",
        f"- **Patterns sécurité résiduels (doit être 0) : {stats['security_pattern_hits']}**",
        f"- **Score de qualité global : {stats['quality_score']}/100**",
        "",
        "## Exemples de réponses suspectes",
    ]
    for ex in stats["suspect_examples"]:
        lines.append(f"- Q: {ex['instruction'][:80]}... | R: {ex['output'][:80]}")

    lines += [
        "",
        "## Recommandation",
        "Score >= 90 et 0 pattern sécurité → prêt pour fine-tuning.",
        "Sinon : nettoyage supplémentaire requis.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="Dataset")
    args = parser.parse_args()

    entries = load(args.input)
    stats = analyze(entries)
    write_report(stats, args.output, args.title)
    print(json.dumps(stats, indent=2, default=str))
    print(f"[OK] Rapport écrit dans {args.output}")


if __name__ == "__main__":
    main()
