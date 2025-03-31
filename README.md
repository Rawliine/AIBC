# AI & Blockchain Project

## Overview
This project integrates **advanced Artificial Intelligence (AI)** technologies with **blockchain** to explore innovative solutions. The main objective is to develop a **robust infrastructure** for training large-scale AI models while leveraging blockchain for distributed storage, secure transactions, and reward mechanisms (e.g., miners contributing to AI training compute).

The **AI** portion uses **Ray** for **distributed training** (potentially across multiple machines, including WSL2 environments), **PyTorch** for model development, and **Hugging Face**/Transformers. The **blockchain** portion involves **Hardhat** (Ethereum smart contract development framework) and **IPFS** for storing checkpoints.

---

## Table of Contents
1. [Prerequisites](#prerequisites)  
2. [Environment Setup](#environment-setup)  
3. [Tools and Technologies](#tools-and-technologies)  
4. [Observability Tools Setup](#observability-tools-setup)  
5. [Blockchain Environment Setup](#blockchain-environment-setup)  
6. [Multi-Machine Distributed Training](#multi-machine-distributed-training)  
7. [Future Work](#future-work)

---

## Prerequisites
Before starting, ensure you have the following installed:

### System Requirements
- **WSL2** (Windows Subsystem for Linux) on Windows 10/11, or a native Linux system.
- **Ubuntu 20.04 or later** recommended (WSL2, Docker, or bare-metal).

### Software
- **Python 3.10+** (managed via Conda or pyenv).
- **Node.js 18+** and **npm**.
- **Anaconda/Miniconda** for managing Python environments.
- **Git** for version control.
- **Prometheus** and **Grafana** for observability tools.
- **IPFS** (optional) for decentralized checkpoint storage.

---

## Environment Setup

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Step 2: Set Up the Python Environment
1. **Create a Conda environment** with Python 3.10:
   ```bash
   conda create -n my_env python=3.10 -y
   conda activate my_env
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   This includes **PyTorch**, **Ray**, **Transformers**, etc.

3. (Optional) **Check GPU availability**:
   ```python
   import torch
   print("CUDA available:", torch.cuda.is_available())
   if torch.cuda.is_available():
       print("GPU Name:", torch.cuda.get_device_name(0))
   ```

### Step 3: Set Up the Node.js Environment
1. **Install npm dependencies**:
   ```bash
   npm install
   ```
2. **Initialize Hardhat** (if not already):
   ```bash
   npx hardhat
   ```
   When prompted, select "Create an empty hardhat.config.js" or overwrite.

### Step 4: Configure Sensitive Files
1. **Create a `.env` file** at the project root to store secrets:
   ```bash
   touch .env
   ```
   Example content:
   ```bash
   ALCHEMY_URL="https://polygon-mumbai.g.alchemy.com/v2/your-api-key"
   PRIVATE_KEY="your-private-key"
   ```
2. **Update** `.gitignore` to ensure `.env` is ignored.

### Step 5: Set Up Prometheus and Grafana (Optional)
1. **Install** Prometheus & Grafana:
   ```bash
   sudo apt install prometheus grafana
   ```
2. **Start the services**:
   ```bash
   sudo systemctl start prometheus
   sudo systemctl start grafana-server
   ```
3. Configure a **Prometheus data source** in Grafana via [http://localhost:3000](http://localhost:3000).

---

## Tools and Technologies

### AI/ML
- **Python 3.10+**
- **PyTorch** (for model training)
- **Ray** (for distributed computing/training)
- **Hugging Face Transformers** (for tokenizers, pretrained models, etc.)

### Blockchain
- **Hardhat** (for compiling & deploying smart contracts)
- **Node.js** and **npm** (for managing blockchain scripts)
- **IPFS** (for decentralized checkpoint storage, optional)

### Observability
- **Prometheus** & **Grafana** (for metrics, GPU/CPU usage, cluster status)

---

## Multi-Machine Distributed Training
## Setting up Ray Cluster on WSL with Multiple Machines

## 1. Port Forwarding Setup

### On Head Node (192.168.1.29)
In PowerShell (as administrator):
```powershell
# GCS server
netsh interface portproxy add v4tov4 listenaddress=192.168.1.29 listenport=6379 connectaddress=172.17.33.96 connectport=6379

# Object Manager
netsh interface portproxy add v4tov4 listenaddress=192.168.1.29 listenport=8076 connectaddress=172.17.33.96 connectport=8076

# Node Manager
netsh interface portproxy add v4tov4 listenaddress=192.168.1.29 listenport=8077 connectaddress=172.17.33.96 connectport=8077

# Runtime Env Agent
netsh interface portproxy add v4tov4 listenaddress=192.168.1.29 listenport=8078 connectaddress=172.17.33.96 connectport=8078

# Dashboard
netsh interface portproxy add v4tov4 listenaddress=192.168.1.29 listenport=8265 connectaddress=172.17.33.96 connectport=8265

# Ray Client Server
netsh interface portproxy add v4tov4 listenaddress=192.168.1.29 listenport=10001 connectaddress=172.17.33.96 connectport=10001

# Worker ports (using a smaller range for testing)
for ($port = 10000; $port -le 10004; $port++) {
    netsh interface portproxy add v4tov4 listenaddress=192.168.1.29 listenport=$port connectaddress=172.17.33.96 connectport=$port
}
```

### On Worker Node (192.168.1.17)
In PowerShell (as administrator):
```powershell
# GCS server
netsh interface portproxy add v4tov4 listenaddress=192.168.1.17 listenport=6379 connectaddress=172.28.94.168 connectport=6379

# Object Manager
netsh interface portproxy add v4tov4 listenaddress=192.168.1.17 listenport=8076 connectaddress=172.28.94.168 connectport=8076

# Node Manager
netsh interface portproxy add v4tov4 listenaddress=192.168.1.17 listenport=8077 connectaddress=172.28.94.168 connectport=8077

# Runtime Env Agent
netsh interface portproxy add v4tov4 listenaddress=192.168.1.17 listenport=8078 connectaddress=172.28.94.168 connectport=8078

# Dashboard
netsh interface portproxy add v4tov4 listenaddress=192.168.1.17 listenport=8265 connectaddress=172.28.94.168 connectport=8265

# Ray Client Server
netsh interface portproxy add v4tov4 listenaddress=192.168.1.17 listenport=10001 connectaddress=172.28.94.168 connectport=10001

# Worker ports (using a smaller range for testing)
for ($port = 10000; $port -le 10004; $port++) {
    netsh interface portproxy add v4tov4 listenaddress=192.168.1.17 listenport=$port connectaddress=172.28.94.168 connectport=$port
}
```

## 2. Firewall Rules

### On Both Machines
In PowerShell (as administrator):
```powershell
# Check existing rules
Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Ray*" }

# Remove existing rules if needed
Remove-NetFirewallRule -DisplayName "Ray Cluster*"

# Create new rules
New-NetFirewallRule -DisplayName "Ray Cluster Inbound" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 6379,8076,8077,8265
New-NetFirewallRule -DisplayName "Ray Cluster Outbound" -Direction Outbound -Action Allow -Protocol TCP -RemotePort 6379,8076,8077,8265
```

## 3. Environment Variables

### On Both Machines
In WSL:
```bash
# Set environment variables for network stability
export RAY_health_check_timeout_ms=99999999999
export RAY_grpc_keepalive_time_ms=99999999999
export RAY_grpc_client_keepalive_time_ms=99999999999
export RAY_grpc_client_keepalive_timeout_ms=99999999999
export RAY_health_check_initial_delay_ms=99999999999
export RAY_health_check_period_ms=99999999999
export RAY_health_check_timeout_ms=99999999999
export RAY_health_check_failure_threshold=10
```

## 4. Starting Ray

### On Head Node
In WSL:
```bash
# Stop any existing Ray processes
ray stop
sudo service redis-server stop

# Start Ray head node
ray start --head --port=6379 --object-manager-port=8076 --node-manager-port=8077 --dashboard-host=0.0.0.0 --dashboard-port=8265 --node-ip-address=0.0.0.0 --redis-password="123456"
```

### On Worker Node
In WSL:
```bash
# Stop any existing Ray processes
ray stop
sudo service redis-server stop

# Start Ray worker
ray start --address=192.168.1.29:6379 --object-manager-port=8076 --node-manager-port=8077 --node-ip-address=0.0.0.0 --redis-password="123456"
```

### Overview
We use **Ray** to orchestrate multi-machine training. **Ray** can automatically distribute data or gradients across multiple workers. For complex transformer training, you can spawn multiple **Ray workers** that each process a partition of your dataset.

1. **Start Ray Head** on a primary machine (or WSL2 instance):
   ```bash
   ray stop
   ray start --head --port=6379 --node-ip-address=0.0.0.0
   ```
   - `--node-ip-address=0.0.0.0` ensures Ray binds to all interfaces.
   - You might also use `--ray-client-server-port=10001` for Ray Client connections.

2. **Port Forwarding on WSL2** (if applicable):
   - Run in **PowerShell (Admin)** on Windows:
     ```powershell
     netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=6379 connectaddress=172.17.xx.xx connectport=6379
     netsh advfirewall firewall add rule name="Allow Ray 6379" dir=in action=allow protocol=TCP localport=6379
     ```
   - This allows external machines to connect to `WSL2` on port `6379`.

3. **Join from a Worker Node**:
   ```bash
   ray start --address='x.x.x.x:6379'
   ```
   - Replace `x.x.x.x` with the **IP** of your head node (e.g., your Windows IP if bridging through WSL2).

4. **Run the Training Script**:
   ```bash
   python train/trainer.py
   ```

5. **Verify cluster status**:
   ```bash
   ray status
   ```

---

## Future Work
- Implement **multi-GPU gradient aggregation**.
- Add **Zero-Knowledge Proofs (ZK)** for decentralized AI verification.
- Extend **smart contract automation** for AI miner rewards.
- Explore **cross-chain interoperability**.

---

## Monitoring and Metrics

The project includes a comprehensive monitoring setup using Prometheus and Grafana for real-time metrics visualization.

### Components

1. **Ray Dashboard**
   - Access at: `http://localhost:8265`
   - Provides real-time cluster status, logs, and job information
   - Metrics endpoint: `http://localhost:8081/metrics`

2. **Prometheus**
   - Access at: `http://localhost:9090`
   - Scrapes metrics from Ray cluster
   - Configuration: `/etc/prometheus/prometheus.yml`
   - Default scrape interval: 15s

3. **Grafana**
   - Access at: `http://localhost:3000`
   - Default credentials: admin/admin
   - Visualizes metrics collected by Prometheus
   - Custom dashboard for Ray metrics visualization

### Setup Instructions

1. **Start IPFS Daemon**
   ```bash
   ipfs daemon
   ```

2. **Start Prometheus**
   ```bash
   sudo -u prometheus /usr/local/bin/prometheus --config.file /etc/prometheus/prometheus.yml --storage.tsdb.path /var/lib/prometheus/
   # Press Ctrl+Z, then bg to run in background
   ```

3. **Start Training with Monitoring**
   ```bash
   python -m train.trainer
   ```

4. **Access Dashboards**
   - Ray Dashboard: `http://localhost:8265`
   - Prometheus: `http://localhost:9090`
   - Grafana: `http://localhost:3000`

### Available Metrics

The system exposes various Ray metrics including:
- CPU utilization
- Memory usage
- Worker status
- Task/actor counts
- Object store metrics

### Troubleshooting

1. **Port Conflicts**
   - Ray metrics: Port 8081
   - IPFS Gateway: Port 8080
   - Prometheus: Port 9090
   - Grafana: Port 3000

2. **Service Status**
   - Check Prometheus targets: `http://localhost:9090/targets`
   - Verify Ray metrics endpoint: `curl http://localhost:8081/metrics`
   - Check Grafana data source: Configuration > Data Sources > Prometheus

3. **Common Issues**
   - If Prometheus shows "404 Not Found" for Ray metrics, verify the metrics port in `train/trainer.py`
   - If Grafana shows no data, check Prometheus targets and time range settings
   - If services don't start, check for port conflicts and running processes

### Post-Restart Steps

After system restart, the following services need to be manually started:
1. IPFS Daemon
2. Prometheus
3. Training script

Grafana starts automatically as a system service.

---

**For troubleshooting and contributions, see the issues tab!** 🚀
