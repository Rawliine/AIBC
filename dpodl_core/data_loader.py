# dpodl_core/data_loader.py
import os
from typing import List, Any, Dict

import torch
from torch.utils.data import random_split
from datasets import load_dataset, DatasetDict, Dataset
from transformers import AutoTokenizer
import logging

import ray

logger = logging.getLogger(__name__)

@ray.remote
def load_partition(dataset, indices: List[int]):
    """
    Charge une partition spécifique du dataset Hugging Face en utilisant des indices.
    Retourne une sous-partie du dataset (toujours au format Dataset HF).
    """
    subset = dataset.select(indices)
    return subset

def load_dataset_and_partition(
    dataset_name: str,
    num_workers: int, 
    batch_size: int = 64, 
    split_ratio=0.8,
    dataset_path_override: str = None,
    num_train_samples: int = None,
    num_val_samples: int = None
) -> Dict[str, Any]:
    """
    - Charge le dataset (e.g., AG News) depuis huggingface datasets ou un chemin local.
    - Permet de limiter le nombre d'échantillons pour train/val.
    - Tokenize les données (Hugging Face).
    - Partitionne le dataset en num_workers (indices).
    - Retourne un dict contenant:
        'train_partitions': liste des partitions (Dataset HF) pour chaque worker
        'val_dataset': dataset de validation (HF)
        'tokenizer': pour d'éventuels usages
        'vocab': un mapping token->idx si besoin.

    split_ratio=0.8 => 80% train, 20% val (si num_samples non spécifié).
    """
    
    if dataset_path_override and os.path.exists(dataset_path_override):
        logger.info(f"Loading dataset from local path: {dataset_path_override}")
        # Assumes the local path contains pre-split train/test or a single dataset
        # For simplicity, let's assume it might be a directory loadable by `load_dataset`
        # or specific files. This part might need refinement based on tiny dataset structure.
        try:
            # Attempt to load as if it's a directory with standard HF dataset files
            # (e.g., csv, json, arrow files, or a dataset_infos.json)
            dataset = load_dataset(dataset_path_override)
            if isinstance(dataset, DatasetDict):
                # If it loads as a DatasetDict, try to get a 'train' split, then 'test'
                # This logic assumes standard splits if loading a pre-split tiny dataset
                if "train" in dataset and "test" in dataset:
                    logger.info("Found 'train' and 'test' splits in local dataset_dict.")
                    full_train_dataset = dataset["train"]
                    full_val_dataset = dataset["test"]
                elif "train" in dataset:
                    logger.warning("Local dataset has 'train' split but no 'test' split. Splitting train for validation.")
                    temp_dataset_dict = dataset["train"].train_test_split(test_size=1-split_ratio)
                    full_train_dataset = temp_dataset_dict["train"]
                    full_val_dataset = temp_dataset_dict["test"]
                else:
                    raise ValueError("Local dataset loaded as DatasetDict, but no 'train' split found.")
            elif isinstance(dataset, Dataset):
                logger.warning("Local dataset loaded as a single Dataset. Splitting for train/val.")
                dataset_dict_temp = dataset.train_test_split(test_size=1-split_ratio)
                full_train_dataset = dataset_dict_temp["train"]
                full_val_dataset = dataset_dict_temp["test"]
            else:
                raise ValueError(f"Unsupported dataset type loaded from path: {type(dataset)}")

        except Exception as e:
            logger.error(f"Failed to load dataset from local path {dataset_path_override}: {e}. Falling back to Hugging Face hub.")
            # Fallback to HF Hub if local loading fails or path not provided
            dataset_hf = load_dataset(dataset_name, split="train") # Default to loading 'train' from HF
            dataset_dict_hf = dataset_hf.train_test_split(test_size=1-split_ratio)
            full_train_dataset = dataset_dict_hf["train"]
            full_val_dataset = dataset_dict_hf["test"]
    else:
        if dataset_path_override:
            logger.warning(f"Local dataset path {dataset_path_override} not found. Loading {dataset_name} from Hugging Face hub.")
        else:
            logger.info(f"Loading {dataset_name} from Hugging Face hub.")
        dataset_hf = load_dataset(dataset_name, split="train")
        dataset_dict_hf = dataset_hf.train_test_split(test_size=1-split_ratio)
        full_train_dataset = dataset_dict_hf["train"]
        full_val_dataset = dataset_dict_hf["test"]

    # Sub-sample if requested
    if num_train_samples is not None and num_train_samples < len(full_train_dataset):
        logger.info(f"Sub-sampling train dataset to {num_train_samples} samples.")
        full_train_dataset = full_train_dataset.select(range(num_train_samples))
    
    if num_val_samples is not None and num_val_samples < len(full_val_dataset):
        logger.info(f"Sub-sampling validation dataset to {num_val_samples} samples.")
        full_val_dataset = full_val_dataset.select(range(num_val_samples))

    # Tokenizer Hugging Face
    tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

    # Tokenization
    # Important: Use with_indices=True if available and needed for reproducibility of shuffles later, or handle shuffles carefully
    tokenized_train_dataset = full_train_dataset.map(tokenize_function, batched=True, remove_columns=["text"])
    tokenized_val_dataset = full_val_dataset.map(tokenize_function, batched=True, remove_columns=["text"])

    vocab = {token: idx for idx, token in enumerate(tokenizer.get_vocab().keys())}

    # Partitionner les indices pour chaque worker
    train_size = len(tokenized_train_dataset)
    train_indices = list(range(train_size))
    if num_workers > 0: # Ensure num_workers is positive
        chunk_size = train_size // num_workers if num_workers > 0 else train_size
    else: # Should not happen if called from trainer with num_workers > 0
        logger.warning("num_workers is 0 or negative, assigning all data to a single logical partition.")
        chunk_size = train_size
        num_workers = 1 # Treat as 1 worker for partitioning logic

    splitted_indices = []
    for i in range(num_workers):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size
        if i == num_workers - 1: # Last worker takes the remainder
            end_idx = train_size
        splitted_indices.append(train_indices[start_idx:end_idx])
    
    # Filter out empty index lists, which can happen if num_workers > train_size
    splitted_indices = [indices for indices in splitted_indices if indices]
    if not splitted_indices and train_size > 0:
        logger.warning("Splitted indices resulted in empty list, assigning all to one partition.")
        splitted_indices = [train_indices]
    elif not splitted_indices and train_size == 0:
        logger.warning("Train dataset is empty, no partitions to create.")
        # Return empty partitions and val set to avoid errors downstream
        return {
            "vocab": vocab,
            "tokenizer": tokenizer,
            "train_partitions": [],
            "val_dataset": tokenized_val_dataset
        }


    # Lancer Ray pour charger chaque partition
    futures = [
        load_partition.remote(tokenized_train_dataset, indices)
        for indices in splitted_indices
    ]
    train_partitions = ray.get(futures)

    return {
        "vocab": vocab,
        "tokenizer": tokenizer,
        "train_partitions": train_partitions,
        "val_dataset": tokenized_val_dataset
    }
