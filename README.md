# AI & Blockchain Project

## Overview
This project integrates advanced Artificial Intelligence (AI) technologies with blockchain to explore innovative solutions. The main objective is to develop a robust infrastructure for training large-scale AI models while leveraging blockchain for distributed storage and secure transactions.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Tools and Technologies](#tools-and-technologies)
4. [Observability Tools Setup](#observability-tools-setup)
5. [Blockchain Environment Setup](#blockchain-environment-setup)
6. [Future Work](#future-work)

---

## Prerequisites
Before starting, ensure you have the following installed:

### System Requirements
- **WSL2** (Windows Subsystem for Linux) or a native Linux system.
- **Ubuntu 20.04 or later**.

### Software
- **Python 3.10+** (managed via Conda or pyenv).
- **Node.js 18+** and **npm**.
- **Anaconda/Miniconda** for managing Python environments.
- **Git** for version control.
- **Prometheus** and **Grafana** for observability tools.

---

## Environment Setup

### Step 1: Clone the Repository
Clone this Git repository to get started:
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Step 2: Set Up the Python Environment
1. Create a Conda environment with Python 3.10:
   ```bash
   conda create -n my_env python=3.10 -y
   conda activate my_env
   ```

2. Install the Python dependencies listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify that PyTorch detects your GPU:
   ```python
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   print(f"GPU Name: {torch.cuda.get_device_name(0)}")
   ```

### Step 3: Set Up the Node.js Environment
1. Install npm dependencies:
   ```bash
   npm install
   ```

2. Initialize Hardhat in the project:
   ```bash
   npx hardhat
   ```
   When prompted, select "Create an empty hardhat.config.js".

### Step 4: Configure Sensitive Files
1. Create a `.env` file at the project root to store API keys and secrets:
   ```bash
   touch .env
   ```
   Example content:
   ```
   ALCHEMY_URL="https://polygon-mumbai.g.alchemy.com/v2/your-api-key"
   PRIVATE_KEY="your-private-key"
   ```

### Step 5: Set Up Prometheus and Grafana
1. Install Prometheus and Grafana on your system:
   ```bash
   sudo apt install prometheus grafana
   ```

2. Start the services:
   ```bash
   sudo systemctl start prometheus
   sudo systemctl start grafana-server
   ```

3. Configure a Prometheus data source in Grafana via [http://localhost:3000](http://localhost:3000).

---

## Tools and Technologies
### AI
- **Python 3.10+**
- **PyTorch 2.0+**
- **Ray** for distributed orchestration

### Blockchain
- **Hardhat** for compiling and deploying smart contracts
- **Node.js** and **npm** for managing blockchain dependencies

### Observability
- **Prometheus** and **Grafana** for monitoring GPU utilization and network metrics

---
