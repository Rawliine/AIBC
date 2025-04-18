import json
import os
import torch
import deepspeed
import ray
from ray.train.torch import TorchTrainer
from ray.air.config import ScalingConfig
import torch.nn as nn
import torch.optim as optim

class SimpleModel(nn.Module):
    def __init__(self):
        super(SimpleModel, self).__init__()
        self.fc = nn.Linear(10, 1)

    def forward(self, x):
        return self.fc(x)

def train_func(config):
    model = SimpleModel()
    optimizer = optim.Adam(model.parameters(), lr=0.0001)

    # Construire un chemin absolu basé sur le script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    ds_config_path = os.path.join(script_dir, "ds_config.json")

    # Charger le JSON en dict
    with open(ds_config_path, "r") as f:
        ds_config = json.load(f)

    model_engine, optimizer, _, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        optimizer=optimizer,
        config=ds_config
    )

    # IMPORTANT: déplacer les données sur le même device que le modèle
    device = model_engine.device
    data = torch.randn(32, 10).to(device).half() 
    target = torch.randn(32, 1).to(device).half() 

    for _ in range(10):
        output = model_engine(data)
        loss = ((output - target) ** 2).mean()
        model_engine.backward(loss)
        model_engine.step()

if __name__ == "__main__":
    ray.init()
    trainer = TorchTrainer(
        train_loop_per_worker=train_func,
        scaling_config=ScalingConfig(
            num_workers=1,
            use_gpu=torch.cuda.is_available()
        )
    )
    trainer.fit()
    ray.shutdown()