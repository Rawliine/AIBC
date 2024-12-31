# train/utils.py
import torch
import logging
import psutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trainer_utils")

def log_memory_usage_gpu(msg=""):
    """
    Log la mémoire GPU disponible/utilisée si on a une carte NVIDIA.
    """
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / (1024 ** 2)
        max_alloc = torch.cuda.max_memory_allocated() / (1024 ** 2)
        logger.info(f"[GPU Memory] {msg} Current alloc: {alloc:.2f} MB, Max alloc: {max_alloc:.2f} MB")

def log_memory_usage_cpu(msg=""):
    """
    Log la mémoire CPU globale du système
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info().rss / (1024 ** 2)
    logger.info(f"[CPU Memory] {msg} RSS: {mem_info:.2f} MB")
