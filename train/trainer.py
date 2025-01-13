import os
import torch
import time
import ray

from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig, RunConfig
from ray.train import Checkpoint

# On importe DeeperTransformer (plus gros modèle) plutôt que SimpleTransformer
from train.model import DeeperTransformer
from train.utils import (
    logger,
    log_memory_usage_cpu,
    log_memory_usage_gpu,
    save_checkpoint,
    load_checkpoint,
    collate_batch
)
from train.data_loader import load_dataset_and_partition

def worker_train_loop(config):
    """
    Fonction exécutée par chaque worker Ray.
    - Récupère la partition
    - Boucle sur epochs, mini-batches
    - Fait forward/backward
    - Sauvegarde un checkpoint
    """
    import torch.distributed as dist
    from ray.train import get_context

    train_context = get_context()
    rank = train_context.get_world_rank()
    world_size = train_context.get_world_size()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    partitions = config["partitions"]   # liste de partitions => partitions[rank]
    seq_len = config["seq_len"]
    batch_size = config["batch_size"]
    epochs = config["epochs"]
    lr = config["lr"]
    embed_dim = config["embed_dim"]
    num_heads = config["num_heads"]
    num_layers = config["num_layers"]
    checkpoint_path = config["checkpoint_path"]

    # Construire le modèle plus profond
    model = DeeperTransformer(
        vocab_size=30522,  # taille approx. du vocab BERT
        embed_dim=embed_dim,
        seq_len=seq_len,
        num_heads=num_heads,
        num_layers=num_layers,
        num_classes=4
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # Charger un éventuel checkpoint
    start_epoch, prev_loss = load_checkpoint(checkpoint_path, model, optimizer)

    # Récupérer la partition associée à ce worker
    my_dataset = partitions[rank]
    my_data_list = list(my_dataset)  # Convertir en liste pour itérer

    # On peut shuffle localement
    rng = torch.Generator().manual_seed(42 + rank)

    for epoch in range(start_epoch, epochs):
        t0 = time.time()
        model.train()
        # shuffle local
        indices = torch.randperm(len(my_data_list), generator=rng).tolist()
        my_data_list_shuffled = [my_data_list[i] for i in indices]

        epoch_loss = 0.0
        step_count = 0

        for start_idx in range(0, len(my_data_list_shuffled), batch_size):
            batch_slice = my_data_list_shuffled[start_idx : start_idx + batch_size]
            texts_t, labels_t = collate_batch(batch_slice, seq_len=seq_len)
            texts_t = texts_t.to(device)
            labels_t = labels_t.to(device)

            optimizer.zero_grad()
            logits = model(texts_t)
            loss = torch.nn.functional.cross_entropy(logits, labels_t)
            loss.backward()

            # (Optionnel) Agrégation de gradients si multi-GPU : 
            # for p in model.parameters():
            #     if p.grad is not None:
            #         dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)
            #         p.grad /= world_size

            optimizer.step()

            epoch_loss += loss.item()
            step_count += 1

            if step_count % 100 == 0:
                logger.info(f"[Worker {rank}] Epoch {epoch} Step {step_count} - loss={loss.item():.4f}")
                log_memory_usage_cpu(f"Worker {rank}")
                log_memory_usage_gpu(f"Worker {rank}")

        epoch_loss /= max(step_count, 1)
        dt = time.time() - t0
        logger.info(f"[Worker {rank}] Finished epoch {epoch} with loss={epoch_loss:.4f} in {dt:.1f}s")

        # Sauvegarder checkpoint
        save_checkpoint(epoch + 1, model, optimizer, epoch_loss, checkpoint_path)

    logger.info(f"[Worker {rank}] Training complete.")

def run_training(
    num_workers: int = 1,        # Sur un seul GPU, souvent plus simple de mettre 1 worker
    epochs: int = 5,
    batch_size: int = 256,      # Augmenté
    seq_len: int = 128,         # Augmenté
    embed_dim: int = 256,       # Augmenté
    num_heads: int = 8,         # Plus de têtes
    num_layers: int = 6,        # 6 blocs
    checkpoint_path: str = "checkpoint_deeper.pt"
):
    """
    Fonction orchestrant l'entraînement distribué (local) avec Ray.
    - on charge/partitionne le dataset
    - on configure TorchTrainer
    """
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)

    # Charger dataset & partitions
    data_loaded = load_dataset_and_partition(num_workers, batch_size)

    partitions = data_loaded["train_partitions"]
    # val_dataset = data_loaded["val_dataset"]  # si on veut une val

    # Config envoyée à chaque worker
    train_loop_config = {
        "partitions": partitions,
        "seq_len": seq_len,
        "batch_size": batch_size,
        "epochs": epochs,
        "lr": 1e-3,
        "embed_dim": embed_dim,
        "num_heads": num_heads,
        "num_layers": num_layers,
        "checkpoint_path": checkpoint_path,
    }

    trainer = TorchTrainer(
        train_loop_per_worker=worker_train_loop,
        train_loop_config=train_loop_config,
        scaling_config=ScalingConfig(
            num_workers=num_workers,
            use_gpu=torch.cuda.is_available(),
            # Sur 1 GPU, on donne 1 GPU au worker
            resources_per_worker={"CPU": 0.25, "GPU": 0.25},
        ),
        run_config=RunConfig(
            name="AGNews_DeeperTransformer",
            storage_path=f"file://{os.path.abspath('ray_results')}"
        ),
    )

    result = trainer.fit()
    logger.info(f"Training done. Ray result: {result}")

if __name__ == "__main__":
    run_training(
        num_workers=3,
        epochs=5,
        batch_size=256,
        seq_len=128,
        embed_dim=256,
        num_heads=8,
        num_layers=6,
        checkpoint_path="checkpoint_deeper.pt"
    )
