import os
import torch
import ray
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig

from train.data_loader import load_dataset_distributed
from train.model import SimpleTransformer
from train.utils import log_memory_usage_gpu, log_memory_usage_cpu, logger

def train_loop_per_worker(config):
    """
    Fonction de training exécutée par chaque worker Ray.
    - Récupère sa partition de données
    - Fait un forward/backward sur la partition
    - Simule une agrégation de gradients
    """
    rank = ray.train.get_context().get_world_rank()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # On reconstruit un mini-modèle identique sur chaque worker
    model = SimpleTransformer(
        vocab_size=config["vocab_size"], 
        embed_dim=config["embed_dim"], 
        seq_len=config["seq_len"]
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"])

    # Chargement local de la partition (simulé ci-dessous en dur).
    # Dans un flux plus complexe, on pourrait charger la partition
    # associée au worker (ex: partitions[rank]).
    data_partition = config["partitions"][rank]

    # On simule un batch unique (32 tokens x batch_size=8, par ex.)
    # Dans la vraie vie, on itèrerait sur data_partition en mini-batches
    batch_size = 8
    dummy_tokens = torch.randint(0, config["vocab_size"], (batch_size, config["seq_len"]), device=device)
    # Labels fictifs
    dummy_labels = torch.randn(batch_size, device=device)

    log_memory_usage_cpu(f"Worker {rank} - Avant forward/backward")
    log_memory_usage_gpu(f"Worker {rank} - Avant forward/backward")

    model.train()
    # Forward
    outputs = model(dummy_tokens)
    loss = torch.nn.functional.mse_loss(outputs, dummy_labels)
    # Backward
    optimizer.zero_grad()
    loss.backward()

    # -- ICI : on simule la réduction/all-reduce des gradients entre workers --
    #   Sur un vrai cluster, on utiliserait torch.distributed.all_reduce
    #   ou Ray Collectives pour agréger les gradients. Ex. :
    #   for param in model.parameters():
    #       if param.grad is not None:
    #           dist.all_reduce(param.grad.data, op=dist.ReduceOp.SUM)
    #           param.grad.data /= world_size
    # Comme on est en local sur 1 machine, on omet ce passage (ou on l’imite).

    # Update
    optimizer.step()

    log_memory_usage_cpu(f"Worker {rank} - Apres backward/step")
    log_memory_usage_gpu(f"Worker {rank} - Apres backward/step")

    logger.info(f"Worker {rank}: loss = {loss.item():.4f}")

def run_training(num_workers: int = 2):
    """
    Fonction principale orchestrant le data parallelisme sur un GPU unique,
    mais réparti en N workers Ray (simulé).
    """
    # Initialiser Ray globalement
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)

    # Charger le dataset "partitionné"
    partitions = load_dataset_distributed(num_workers)

    trainer = TorchTrainer(
        train_loop_per_worker=train_loop_per_worker,
        # On passe la config qui sera transmise à chaque worker
        train_loop_config={
            "vocab_size": 1000,
            "embed_dim": 128,
            "seq_len": 32,
            "lr": 1e-3,
            "partitions": partitions,
        },
        scaling_config=ScalingConfig(
            num_workers=num_workers,
            resources_per_worker={"CPU": 0.25, "GPU": 0.25},
            use_gpu=torch.cuda.is_available(),  # un GPU si dispo
        ),
    )

    result = trainer.fit()
    logger.info(f"Training terminé. Résultat: {result}")
    ray.shutdown()


if __name__ == "__main__":
    # Exemple: lancer 2 "workers" qui partagent (virtuellement) un seul GPU
    run_training(num_workers=4)
