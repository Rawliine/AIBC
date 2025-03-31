import os
import time
import ray
import torch

# Ray AIR / train
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig, RunConfig
from ray.train import Checkpoint

# On importe DeeperTransformer (gros modèle).
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
    Fonction exécutée sur chaque worker Ray.
    - Récupère sa partition de dataset (config["partitions"][rank])
    - Fait un certain nombre d'epochs
    - Boucle sur des mini-batches
    - Checkpoints local + IPFS
    - (Optionnel) agrégation de gradients en multi-GPU
    - (Optionnel) ZK proof
    """
    import torch.distributed as dist
    from ray.train import get_context

    train_context = get_context()
    rank = train_context.get_world_rank()
    world_size = train_context.get_world_size()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    partitions = config["partitions"]
    seq_len = config["seq_len"]
    batch_size = config["batch_size"]
    epochs = config["epochs"]
    lr = config["lr"]
    embed_dim = config["embed_dim"]
    num_heads = config["num_heads"]
    num_layers = config["num_layers"]
    checkpoint_path = config["checkpoint_path"]

    # Instancier le modèle
    model = DeeperTransformer(
        vocab_size=30522,  # BERT base vocab ~30k
        embed_dim=embed_dim,
        seq_len=seq_len,
        num_heads=num_heads,
        num_layers=num_layers,
        num_classes=4
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # Charger un checkpoint si présent
    start_epoch, prev_loss = load_checkpoint(checkpoint_path, model, optimizer)

    # Récupérer la partition associée au worker
    my_dataset = partitions[rank]
    my_data_list = list(my_dataset)  # Conversion Dataset HF -> list

    # Shuffle local
    rng = torch.Generator().manual_seed(42 + rank)

    # Ajouter validation pour détecter la triche
    validation_batches = []
    if config.get("enable_validation", False):
        # Sélectionner ~5% des lots pour validation
        validation_indices = set(torch.randperm(len(my_data_list))[:int(len(my_data_list) * 0.05)].tolist())
        
        for idx in validation_indices:
            batch = my_data_list[idx]
            # Calculer et enregistrer les gradients pour ce lot
            texts_t, labels_t = collate_batch([batch], seq_len=seq_len)
            texts_t, labels_t = texts_t.to(device), labels_t.to(device)
            
            optimizer.zero_grad()
            logits = model(texts_t)
            loss = torch.nn.functional.cross_entropy(logits, labels_t)
            loss.backward()
            
            # Stocker les gradients pour validation
            gradients = {name: param.grad.clone().detach() for name, param in model.named_parameters() 
                        if param.grad is not None}
            
            validation_batches.append({
                "batch_idx": idx,
                "texts": texts_t.cpu(),
                "labels": labels_t.cpu(),
                "gradients": gradients
            })
    
    # Envoyer les données de validation au coordinateur
    if validation_batches:
        train_context.report({"validation_data": validation_batches, "worker_rank": rank})

    try:
        for epoch in range(start_epoch, epochs):
            t0 = time.time()
            model.train()

            # Shuffle
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

                # Optionnel: agrégation de gradients multi-GPU
                # if world_size > 1:
                #     for p in model.parameters():
                #         if p.grad is not None:
                #             dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)
                #             p.grad /= world_size

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

            # Sauvegarder checkpoint local + IPFS
            cid = save_checkpoint(epoch + 1, model, optimizer, epoch_loss, checkpoint_path)
            logger.info(f"[Worker {rank}] IPFS CID for epoch {epoch} checkpoint: {cid}")

            # (Optionnel) ZK-Proof : générer la preuve qu'on a fait l'epoch
            # generate_zk_proof_of_training(...)

    except Exception as e:
        logger.error(f"Worker {rank} crashed with error: {e}")
        # Sauvegarder l'état actuel avant de quitter
        emergency_cid = save_checkpoint(epoch, model, optimizer, epoch_loss, 
                                      f"emergency_{checkpoint_path}")
        logger.info(f"Emergency checkpoint saved with CID: {emergency_cid}")
        # Notifier le coordinateur
        train_context.report({"status": "crashed", "emergency_cid": emergency_cid})
        raise

    logger.info(f"[Worker {rank}] Training complete.")

def run_training(
    num_workers: int = 1,
    epochs: int = 5,
    batch_size: int = 256,
    seq_len: int = 128,
    embed_dim: int = 256,
    num_heads: int = 8,
    num_layers: int = 6,
    checkpoint_path: str = "checkpoint_deeper.pt"
):
    """
    Lance l'entraînement distribué (ou local) via Ray.
    - Charge un dataset AG News tokenisé
    - Partitionne pour num_workers
    - Crée un TorchTrainer
    - Entraîne un DeeperTransformer
    - Checkpoints => local + IPFS

    Pour un entraînement multi-machines, assurez-vous de démarrer un cluster Ray :
      1) Sur le noeud "head" : 
         ray start --head --port=6379
      2) Sur les noeuds "workers" : 
         ray start --address='ip_du_head:6379'
      3) Dans ce script Python, ray.init(address='auto') se connectera au cluster.
    """
    # --- Modification ici : on se connecte à un cluster Ray s'il existe déjà. ---
    if not ray.is_initialized():
        # Check if a specific address is provided (e.g., via env var RAY_ADDRESS)
        # If not, ray.init() will start a local cluster.
        # If RAY_ADDRESS is set, ray.init(address='auto') will try to connect.
        ray.init(address="auto" if os.environ.get("RAY_ADDRESS") else None, 
                 ignore_reinit_error=True, 
                 include_dashboard=True,
                 _metrics_export_port=8081  # Expose les métriques pour Prometheus
                )

    # Charger dataset & partitions
    data_loaded = load_dataset_and_partition(num_workers, batch_size)
    partitions = data_loaded["train_partitions"]
    # val_dataset = data_loaded["val_dataset"]  # si on veut val

    # Config qu'on envoie aux workers
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

    # Création du TorchTrainer
    trainer = TorchTrainer(
        train_loop_per_worker=worker_train_loop,
        train_loop_config=train_loop_config,
        scaling_config=ScalingConfig(
            num_workers=num_workers,
            use_gpu=torch.cuda.is_available(),
            # Exemple de ressources : on attribue 0.25 CPU et 0.25 GPU par worker,
            # ajustez selon vos besoins.
            resources_per_worker={"CPU": 0.25, "GPU": 0.25},
            # Vous pouvez explicitement définir un backend si nécessaire, par ex.:
            # backend="nccl" si vous avez des GPU NVIDIA et un cluster homogène.
            # backend="gloo"
        ),
        run_config=RunConfig(
            name="AGNews_DeeperTransformer",
            # Stockage Ray local : file:// + chemin absolu
            storage_path=f"file://{os.path.abspath('ray_results')}"
        ),
    )

    result = trainer.fit()
    logger.info(f"Training done. Ray result: {result}")

if __name__ == "__main__":
    # Exemple local : 2 workers, 5 epochs
    run_training(
        num_workers=2,
        epochs=5,
        batch_size=256,
        seq_len=128,
        embed_dim=256,
        num_heads=8,
        num_layers=6,
        checkpoint_path="checkpoint_deeper.pt"
    )
