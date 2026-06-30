"""
validate_phi3_financial.py
À placer dans : techcorp-ai-chat/scripts/ia/validate_phi3_financial.py

Rôle (filière IA) :
Valider et optimiser le modèle Phi-3.5-Financial DÉJÀ déployé par la
filière INFRA (via Ollama, Triton ou un serveur maison) avant de le
déclarer "production ready".

Ce script :
  1. Envoie une batterie de prompts financiers types au serveur d'inférence
  2. Mesure la latence par requête
  3. Vérifie que les réponses sont cohérentes (pas vides, pas tronquées,
     contiennent du vocabulaire financier attendu)
  4. Teste différents paramètres d'inférence (température) pour aider
     l'équipe INFRA à choisir la meilleure config
  5. Produit un rapport de validation (livrable demandé)

Compatible Ollama par défaut (http://localhost:11434/api/generate).
Pour Triton ou un serveur maison, adapter la fonction call_model().

Usage :
    python validate_phi3_financial.py --endpoint http://localhost:11434 \
        --model phi3.5-financial --output validation_report.md
"""

import json
import time
import argparse
import urllib.request
from pathlib import Path

# Prompts représentatifs du cas d'usage finance/business
TEST_PROMPTS = [
    "Explique ce qu'est un flux de trésorerie actualisé (DCF).",
    "Quels sont les indicateurs clés pour évaluer la santé financière d'une PME ?",
    "Résume les différences entre obligations et actions pour un investisseur débutant.",
    "Qu'est-ce qu'un ratio d'endettement et comment l'interpréter ?",
    "Donne un exemple de calcul de marge brute pour une entreprise.",
]

# Mots-clés attendus pour vérifier que le modèle reste "dans le sujet" finance
FINANCE_KEYWORDS = [
    "financ", "investi", "entreprise", "marge", "ratio", "actif", "capital",
    "rendement", "risque", "trésorerie", "obligation", "action", "revenu",
]


def call_model(endpoint: str, model: str, prompt: str, temperature: float = 0.3) -> dict:
    """
    Appelle l'API Ollama (/api/generate). Adapter cette fonction si l'équipe
    INFRA utilise Triton (POST /v2/models/<model>/infer) ou un serveur maison.
    """
    url = f"{endpoint}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    start = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    latency = time.time() - start
    return {"text": body.get("response", ""), "latency": latency}


def score_response(prompt: str, response_text: str) -> dict:
    text_lower = response_text.lower()
    has_keyword = any(k in text_lower for k in FINANCE_KEYWORDS)
    is_empty = len(response_text.strip()) == 0
    seems_truncated = response_text.strip().endswith(("...", ",", ":"))
    return {
        "non_empty": not is_empty,
        "on_topic": has_keyword,
        "not_truncated": not seems_truncated,
        "length": len(response_text),
    }


def run_validation(endpoint: str, model: str) -> list:
    results = []
    for prompt in TEST_PROMPTS:
        for temperature in (0.2, 0.7):
            try:
                out = call_model(endpoint, model, prompt, temperature)
                checks = score_response(prompt, out["text"])
                results.append(
                    {
                        "prompt": prompt,
                        "temperature": temperature,
                        "latency_s": round(out["latency"], 2),
                        **checks,
                        "response_preview": out["text"][:200],
                    }
                )
                print(f"[OK] T={temperature} | {round(out['latency'],2)}s | {prompt[:40]}...")
            except Exception as exc:
                results.append(
                    {
                        "prompt": prompt,
                        "temperature": temperature,
                        "error": str(exc),
                    }
                )
                print(f"[ERREUR] {prompt[:40]}... -> {exc}")
    return results


def write_report(results: list, path: Path):
    ok = [r for r in results if r.get("non_empty") and r.get("on_topic")]
    avg_latency = (
        sum(r["latency_s"] for r in results if "latency_s" in r)
        / max(len([r for r in results if "latency_s" in r]), 1)
    )

    lines = [
        "# Rapport de validation — Phi-3.5-Financial",
        "",
        f"- Tests exécutés : {len(results)}",
        f"- Réponses jugées valides (non vides + sur le sujet) : {len(ok)}/{len(results)}",
        f"- Latence moyenne : {round(avg_latency, 2)} s",
        "",
        "## Détail des tests",
        "",
        "| Prompt | Temp | Latence (s) | Non vide | Sur le sujet | Non tronqué |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['prompt'][:40]}... | {r['temperature']} | ERREUR: {r['error']} | | | |")
            continue
        lines.append(
            f"| {r['prompt'][:40]}... | {r['temperature']} | {r['latency_s']} "
            f"| {'✓' if r['non_empty'] else '✗'} | {'✓' if r['on_topic'] else '✗'} "
            f"| {'✓' if r['not_truncated'] else '✗'} |"
        )

    lines += [
        "",
        "## Recommandation paramètres",
        (
            "Comparer la latence et la justesse entre température=0.2 (réponses "
            "plus déterministes, conseillé en production finance) et 0.7 "
            "(réponses plus variées). Privilégier 0.2-0.3 pour un cas d'usage "
            "financier où la précision prime sur la créativité."
        ),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://localhost:11434")
    parser.add_argument("--model", default="phi3.5-financial")
    parser.add_argument("--output", default="validation_report.md", type=Path)
    args = parser.parse_args()

    results = run_validation(args.endpoint, args.model)
    write_report(results, args.output)
    print(f"[OK] Rapport écrit dans {args.output}")


if __name__ == "__main__":
    main()
