"""
finetune_lora_medical.py
À placer dans : techcorp-ai-chat/scripts/ia/finetune_lora_medical.py

Rôle (filière IA) :
Fine-tuner en LoRA un modèle de base (ex: phi3.5, qwen2.5:3b, mistral,
tinyllama — léger pour tenir sur Colab) sur le dataset médical NETTOYÉ
par la filière DATA (medical_dataset/clean.json).

Rappel important du brief : ce modèle est EXPÉRIMENTAL / R&D, pas destiné
à la production, et ne nécessite pas d'être déployé.

Le script utilise Hugging Face `transformers` + `peft` (LoRA) +
`datasets`, standard pour ce type de fine-tuning, pensé pour tourner sur
Google Colab Pro (GPU T4/A100).

Prérequis (à exécuter sur Colab) :
    pip install transformers peft datasets accelerate bitsandbytes

Usage :
    python finetune_lora_medical.py \
        --base_model microsoft/Phi-3.5-mini-instruct \
        --dataset medical_dataset/clean.json \
        --output_dir ./medical_lora_adapter \
        --epochs 3
"""

import json
import argparse
from pathlib import Path

from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import torch


def load_dataset_as_text(path: Path) -> Dataset:
    """
    Charge le JSON nettoyé par la filière DATA (format
    {"instruction", "input", "output"}) et le transforme en un seul champ
    texte au format prompt instruction-tuning, ce que le modèle apprend
    à reproduire pendant le fine-tuning.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))

    def format_example(e):
        if e.get("input"):
            prompt = (
                f"### Instruction:\n{e['instruction']}\n\n"
                f"### Contexte:\n{e['input']}\n\n### Réponse:\n{e['output']}"
            )
        else:
            prompt = f"### Instruction:\n{e['instruction']}\n\n### Réponse:\n{e['output']}"
        return {"text": prompt}

    formatted = [format_example(e) for e in raw]
    return Dataset.from_list(formatted)


def tokenize_function(examples, tokenizer, max_length=512):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=max_length,
        padding="max_length",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", default="microsoft/Phi-3.5-mini-instruct")
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output_dir", default="./medical_lora_adapter")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    args = parser.parse_args()

    print("[1/5] Chargement du tokenizer et du modèle de base (quantisé 4-bit)...")
    # Chargement en 4-bit pour tenir sur un GPU Colab standard (cf. piste
    # "quantization" du brief)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map="auto",
    )
    model = prepare_model_for_kbit_training(model)

    print("[2/5] Configuration LoRA...")
    # r/alpha modérés : suffisant pour un fine-tuning de spécialisation
    # de domaine (médical) sans réentraîner tout le modèle
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()  # vérifie qu'on entraîne bien <1% des poids

    print("[3/5] Préparation du dataset...")
    dataset = load_dataset_as_text(args.dataset)
    tokenized = dataset.map(
        lambda ex: tokenize_function(ex, tokenizer),
        batched=True,
        remove_columns=["text"],
    )
    split = tokenized.train_test_split(test_size=0.1, seed=42)

    print("[4/5] Lancement de l'entraînement...")
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        fp16=True,
        report_to="none",
    )

    collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=split["train"],
        eval_dataset=split["test"],
        data_collator=collator,
    )
    trainer.train()

    print("[5/5] Sauvegarde de l'adaptateur LoRA...")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[OK] Adaptateur LoRA sauvegardé dans {args.output_dir}")
    print("Rappel : modèle expérimental, ne pas déployer en production.")


if __name__ == "__main__":
    main()
