# train/data_loader.py
import os
import ray
from typing import List, Any

@ray.remote
def load_data_partition(index: int, total_partitions: int) -> List[Any]:
    """
    Fonction simulant le chargement d'une partition de dataset.
    Dans la réalité, on chargerait un vrai morceau de dataset (ex: dataset[index::total_partitions]).
    Ici, on simule juste avec des données aléatoires ou un simple range().

    :param index: Index de la partition
    :param total_partitions: Nombre total de partitions
    :return: Liste de "samples"
    """
    # Exemple fictif : chaque partition contient 100 "samples"
    # On stocke juste un range ; dans la vraie vie, ce serait des batchs ou des tensors
    data_partition = list(range(index * 100, (index + 1) * 100))
    return data_partition

def load_dataset_distributed(num_workers: int) -> List[List[Any]]:
    """
    Lance des tâches Ray pour charger/partitionner le dataset en plusieurs morceaux.

    :param num_workers: Nombre de partitions à charger
    :return: Liste de partitions (chacune est une liste de samples)
    """
    # Initialiser Ray si ce n'est pas déjà fait
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)

    # Lancer le chargement en parallèle
    futures = [
        load_data_partition.remote(index=i, total_partitions=num_workers)
        for i in range(num_workers)
    ]
    # Récupérer les résultats
    partitions = ray.get(futures)
    return partitions
