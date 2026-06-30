"""
Nettoyer le dataset médical avant fine-tuning LoRA (filière DATA / R&D).
"""

import json
import argparse
import hashlib
from pathlib import Path

MIN_LEN = 10
MAX_LEN = 4000


def load_dataset(path: Path) -> list:
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def normalize_entry(entry: dict) -> dict | None:
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
    print(f"[INFO] Entrées normalisées : {len(normalized)}")

    valid = [e for e in normalized if is_valid(e)]
    cleaned = dedupe(valid)
    print(f"[INFO] Entrées finales : {len(cleaned)}")

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
    print(f"[OK] Dataset propre : {args.output}")
    print(f"[OK] Log : {log_path}")


if __name__ == "__main__":
    main()
