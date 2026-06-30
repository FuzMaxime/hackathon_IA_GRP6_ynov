"""Tests de performance du modèle médical fine-tuné (R&D)."""

import time
import argparse
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

TEST_QUESTIONS = [
    "J'ai des maux de tête fréquents depuis une semaine, que pourrait-ce être ?",
    "Quels sont les symptômes courants d'une grippe saisonnière ?",
    "Peux-tu m'expliquer ce qu'est l'hypertension artérielle ?",
    "Quelles précautions prendre en cas de fièvre chez un enfant ?",
    "Qu'est-ce que le diabète de type 2 ?",
]


def load_model(base_model: str, lora_adapter: str | None):
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.float16, device_map="auto"
    )
    if lora_adapter:
        model = PeftModel.from_pretrained(model, lora_adapter)
    model.eval()
    return model, tokenizer


def generate(model, tokenizer, prompt: str, max_new_tokens=200) -> dict:
    full_prompt = f"### Instruction:\n{prompt}\n\n### Réponse:\n"
    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)

    start = time.time()
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.4,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    elapsed = time.time() - start

    text = tokenizer.decode(out[0], skip_special_tokens=True)
    response = text.split("### Réponse:")[-1].strip()
    return {"response": response, "time_s": elapsed}


def is_repetitive(text: str, window: int = 6) -> bool:
    words = text.split()
    if len(words) < window * 2:
        return False
    chunks = [tuple(words[i : i + window]) for i in range(len(words) - window)]
    return len(chunks) != len(set(chunks))


def run_tests(model, tokenizer) -> list:
    results = []
    for q in TEST_QUESTIONS:
        out = generate(model, tokenizer, q)
        results.append(
            {
                "question": q,
                "response": out["response"],
                "time_s": round(out["time_s"], 2),
                "length": len(out["response"]),
                "non_empty": len(out["response"].strip()) > 0,
                "repetitive": is_repetitive(out["response"]),
            }
        )
    return results


def write_report(results: list, path: Path):
    n = len(results)
    non_empty = sum(r["non_empty"] for r in results)
    repetitive = sum(r["repetitive"] for r in results)
    avg_len = sum(r["length"] for r in results) / max(n, 1)
    avg_time = sum(r["time_s"] for r in results) / max(n, 1)

    lines = [
        "# Rapport de performance — Modèle médical fine-tuné (LoRA)",
        "",
        f"- Questions testées : {n}",
        f"- Réponses non vides : {non_empty}/{n}",
        f"- Réponses répétitives : {repetitive}/{n}",
        f"- Longueur moyenne : {round(avg_len)} caractères",
        f"- Temps moyen : {round(avg_time, 2)} s",
        "",
        "## Détail",
    ]
    for r in results:
        lines += [f"### {r['question']}", "", r["response"], ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", default="microsoft/Phi-3.5-mini-instruct")
    parser.add_argument("--lora_adapter", default=None)
    parser.add_argument("--output", default="performance_report.md", type=Path)
    args = parser.parse_args()

    model, tokenizer = load_model(args.base_model, args.lora_adapter)
    results = run_tests(model, tokenizer)
    write_report(results, args.output)
    print(f"[OK] Rapport : {args.output}")


if __name__ == "__main__":
    main()
