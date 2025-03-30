# train/utils.py
import os
import psutil
import torch
import logging
import subprocess
import json
import ipfshttpclient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trainer_utils")

def log_memory_usage_gpu(msg=""):
    """
    Log la mémoire GPU utilisée et la mémoire max allouée depuis le début.
    """
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / (1024 ** 2)
        max_alloc = torch.cuda.max_memory_allocated() / (1024 ** 2)
        logger.info(f"[GPU Memory] {msg} Current alloc: {alloc:.2f} MB, Max alloc: {max_alloc:.2f} MB")

def log_memory_usage_cpu(msg=""):
    """
    Log la mémoire CPU (RSS) du process actuel.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info().rss / (1024 ** 2)
    logger.info(f"[CPU Memory] {msg} RSS: {mem_info:.2f} MB")

def save_checkpoint(epoch, model, optimizer, loss, checkpoint_path="checkpoint.pt"):
    """
    Sauvegarde un checkpoint localement :
      - epoch, model_state_dict, optimizer_state_dict, dernier loss
    """
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "loss": loss
    }, checkpoint_path)
    logger.info(f"Checkpoint saved at {checkpoint_path}")

    # Se connecter au daemon IPFS local
    client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    
    # Ajouter le fichier à IPFS
    res = client.add(checkpoint_path)
    cid = res['Hash']
    
    # Enregistrer le CID dans un fichier de suivi
    with open('checkpoint_cids.txt', 'a') as f:
        f.write(f"{epoch},{cid},{checkpoint_path}\n")
        
    return cid

def load_checkpoint(checkpoint_path, model, optimizer):
    """
    Charge un checkpoint local (pour l'instant).
    Renvoie (epoch, loss).
    """
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
    Convertit un batch du dataset HF en tenseurs PyTorch.
      - On s'appuie sur 'example["input_ids"]' et 'example["label"]'
      - Tronque/pad à seq_len si nécessaire

    Retourne (texts_t, labels_t).
    """
    texts = []
    labels = []

    if not isinstance(batch_data, list):
        batch_data = list(batch_data)

    for example in batch_data:
        label = example["label"]   # Normalement 0..3 pour AG News
        input_ids = example["input_ids"]

        if len(input_ids) > seq_len:
            input_ids = input_ids[:seq_len]
        else:
            input_ids += [0] * (seq_len - len(input_ids))

        labels.append(label)
        texts.append(input_ids)

    texts_t = torch.tensor(texts, dtype=torch.long)   # [batch_size, seq_len]
    labels_t = torch.tensor(labels, dtype=torch.long) # [batch_size]
    return texts_t, labels_t
