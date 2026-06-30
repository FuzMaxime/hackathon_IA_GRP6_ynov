"""
Nettoyer le dataset financier — suppression backdoor, credentials et bruit.
Filière DATA + validation CYBER.
"""

import json
import argparse
import hashlib
import re
from pathlib import Path

MIN_LEN = 20
MAX_LEN = 8000

# Patterns identifiés lors de l'audit CYBER (logs + scan datasets)
BACKDOOR_PATTERNS = [
    r"J3\s*SU1S",
    r"P0UP33",
    r"poup[eé]e de cire",
]

CREDENTIAL_PATTERNS = [
    r"admin:\S+",
    r"Pass:\s*\S+",
    r"password:\s*\S+",
    r"Bearer\s+[a-zA-Z0-9._-]{10,}",
    r"root:mysql",
    r"VPN_Secure",
    r"/etc/passwd",
    r"TechCorp_Secret",
]

SUSPICIOUS_MARKERS = [
    "backdoor",
    "compliance-token",
    "enhanced_mode",
    "enable_enhanced",
]


def load_dataset(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_entry(entry: dict) -> dict | None:
    if "conversation" in entry and isinstance(entry["conversation"], list):
        conv = entry["conversation"]
        if len(conv) < 2:
            return None
        instruction = conv[0].get("content", "").strip()
        output = conv[1].get("content", "").strip()
        context = ""
    else:
        instruction = (
            entry.get("instruction")
            or entry.get("question")
            or entry.get("input")
            or ""
        ).strip()
        output = (
            entry.get("output")
            or entry.get("answer")
            or ""
        ).strip()
        context = (entry.get("input") or "").strip()
        if entry.get("question") and entry.get("answer"):
            instruction = entry["question"].strip()
            output = entry["answer"].strip()

    if not instruction or not output:
        return None

    return {
        "instruction": instruction,
        "input": context,
        "output": output,
    }


def is_malicious(blob: str) -> tuple[bool, str]:
    lower = blob.lower()
    for pattern in BACKDOOR_PATTERNS:
        if re.search(pattern, blob, re.IGNORECASE):
            return True, f"backdoor_trigger:{pattern}"
    for pattern in CREDENTIAL_PATTERNS:
        if re.search(pattern, blob, re.IGNORECASE):
            return True, f"credential_leak:{pattern}"
    for marker in SUSPICIOUS_MARKERS:
        if marker in lower:
            return True, f"suspicious_marker:{marker}"
    return False, ""


def is_valid(entry: dict) -> tuple[bool, str]:
    blob = json.dumps(entry, ensure_ascii=False)
    malicious, reason = is_malicious(blob)
    if malicious:
        return False, reason

    total_len = len(entry["instruction"]) + len(entry["output"])
    if total_len < MIN_LEN or total_len > MAX_LEN:
        return False, "length_out_of_bounds"

    return True, "ok"


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
    print(f"[INFO] Entrées brutes : {len(raw)}")

    removed_reasons: dict[str, int] = {}
    normalized = []
    for entry in raw:
        norm = normalize_entry(entry)
        if norm is None:
            removed_reasons["invalid_format"] = removed_reasons.get("invalid_format", 0) + 1
            continue
        valid, reason = is_valid(norm)
        if not valid:
            removed_reasons[reason] = removed_reasons.get(reason, 0) + 1
            continue
        normalized.append(norm)

    cleaned = dedupe(normalized)
    print(f"[INFO] Après filtrage sécurité : {len(normalized)}")
    print(f"[INFO] Après dédoublonnage : {len(cleaned)}")
    print(f"[INFO] Suppressions par motif : {removed_reasons}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    log = {
        "source": str(args.input),
        "raw_count": len(raw),
        "clean_count": len(cleaned),
        "removed_total": len(raw) - len(cleaned),
        "removed_by_reason": removed_reasons,
        "security_scan": "backdoor_triggers_and_credentials_filtered",
    }
    log_path = args.output.with_name(args.output.stem + ".cleaning_log.json")
    log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"[OK] Dataset propre : {args.output}")
    print(f"[OK] Log : {log_path}")


if __name__ == "__main__":
    main()
