# train/data_loader.py

import os
from typing import List, Any, Dict

import torch
from torch.utils.data import random_split
from datasets import load_dataset
from transformers import AutoTokenizer

import ray

@ray.remote
def load_partition(dataset, indices: List[int]):
    """
    Charge une partition spécifique du dataset Hugging Face en utilisant des indices.
    Retourne une sous-partie du dataset (toujours au format HF).
    """
    subset = dataset.select(indices)
    return subset

def load_dataset_and_partition(num_workers: int, batch_size: int = 64, split_ratio=0.8) -> Dict[str, Any]:
    """
    - Charge le dataset AG News depuis `datasets`.
    - Tokenize les données (Hugging Face).
    - Partitionne le dataset en `num_workers` (indices).
    - Retourne un dict contenant:
        - 'train_partitions': liste des partitions (Dataset HF) pour chaque worker.
        - 'val_dataset': dataset de validation (HF).
        - 'tokenizer': pour d'éventuels usages (attention_mask, etc.).
        - 'vocab': un mapping token->idx si on veut l'utiliser plus tard (pas obligatoire).
    """
    # Charger le dataset "train" complet
    dataset = load_dataset("ag_news", split="train")

    # Tokenizer Hugging Face
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    def tokenize_function(examples):
        # On convertit la clé "text" en input_ids/attention_mask
        # padding="max_length" => on pad jusqu'à la longueur max du tokenizer (512)
        # truncation=True      => on tronque >512 
        return tokenizer(examples["text"], padding="max_length", truncation=True)

    # Tokenization
    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    # Simple vocab basé sur le tokenizer (optionnel si on n'utilise que input_ids)
    vocab = {token: idx for idx, token in enumerate(tokenizer.get_vocab().keys())}

    # Séparer en train/val via HF
    dataset_dict = tokenized_dataset.train_test_split(test_size=1 - split_ratio)
    train_dataset = dataset_dict["train"]
    val_dataset = dataset_dict["test"]

    # Partitionner les indices pour chaque worker
    train_size = len(train_dataset)
    train_indices = list(range(train_size))
    chunk_size = train_size // num_workers
    splitted_indices = [train_indices[i * chunk_size : (i + 1) * chunk_size]
                        for i in range(num_workers)]

    # Lancer Ray pour charger chaque partition
    futures = [
        load_partition.remote(train_dataset, indices)
        for indices in splitted_indices
    ]
    train_partitions = ray.get(futures)

    return {
        "vocab": vocab,
        "tokenizer": tokenizer,
        "train_partitions": train_partitions,
        "val_dataset": val_dataset
    }
