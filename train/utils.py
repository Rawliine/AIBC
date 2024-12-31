# train/utils.py

import os
import psutil
import torch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trainer_utils")

def log_memory_usage_gpu(msg=""):
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / (1024 ** 2)
        max_alloc = torch.cuda.max_memory_allocated() / (1024 ** 2)
        logger.info(f"[GPU Memory] {msg} Current alloc: {alloc:.2f} MB, Max alloc: {max_alloc:.2f} MB")

def log_memory_usage_cpu(msg=""):
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info().rss / (1024 ** 2)
    logger.info(f"[CPU Memory] {msg} RSS: {mem_info:.2f} MB")

def save_checkpoint(epoch, model, optimizer, loss, checkpoint_path="checkpoint.pt"):
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": loss
    }, checkpoint_path)
    logger.info(f"Checkpoint saved at {checkpoint_path}")

def load_checkpoint(checkpoint_path, model, optimizer):
    if os.path.isfile(checkpoint_path):
        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        model.load_state_dict(checkpoint["model_state_dict"])
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        epoch = checkpoint["epoch"]
        loss = checkpoint["loss"]
        logger.info(f"Loaded checkpoint from {checkpoint_path} (epoch={epoch}, loss={loss:.4f})")
        return epoch, loss
    else:
        logger.warning(f"No checkpoint found at {checkpoint_path}. Starting fresh.")
        return 0, float("inf")

def collate_batch(batch_data, seq_len=32):
    """
    Convertit un batch HF en tenseurs PyTorch.
    - On s'appuie sur 'example["input_ids"]' et 'example["label"]'
    - Tronque/pad à seq_len si nécessaire
    """
    texts = []
    labels = []

    # batch_data peut être une list[dict], ou un Dataset HF qu'on slice.
    # On convertit en list si besoin:
    if not isinstance(batch_data, list):
        batch_data = list(batch_data)

    for example in batch_data:
        label = example["label"]   # 0..3 pour AG News
        input_ids = example["input_ids"]

        # Tronquer/pad manuellement à seq_len
        if len(input_ids) > seq_len:
            input_ids = input_ids[:seq_len]
        else:
            input_ids += [0] * (seq_len - len(input_ids))

        labels.append(label)
        texts.append(input_ids)

    texts_t = torch.tensor(texts, dtype=torch.long)   # [batch_size, seq_len]
    labels_t = torch.tensor(labels, dtype=torch.long) # [batch_size]

    return texts_t, labels_t
