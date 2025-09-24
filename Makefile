# =============================================================================
# AI & Blockchain Project - Development Makefile
# =============================================================================

.PHONY: help setup dev-up dev-down dev-status logs-ipfs logs-hardhat logs-all
.PHONY: chain deploy test test-e2e trainer clean clear-mempool

# Default Python and package manager
PYTHON := python
PIP := pip

# Directories
LOGS_DIR := logs
SCRIPTS_DIR := scripts
BLOCKCHAIN_DIR := blockchain

# Default target
help:
	@echo "Available targets:"
	@echo "  setup        - Install dependencies (Python + Node.js)"
	@echo "  dev-up       - Start all dev services (IPFS + Hardhat + Deploy)"
	@echo "  dev-down     - Stop all dev services and clean up"
	@echo "  dev-status   - Check status of dev services"
	@echo "  trainer      - Run the D-PoDL trainer"
	@echo "  logs-ipfs    - Tail IPFS daemon logs"
	@echo "  logs-hardhat - Tail Hardhat node logs"
	@echo "  logs-all     - Tail all service logs"
	@echo "  test         - Run all tests (Python + Solidity)"
	@echo "  test-e2e     - Run end-to-end scenario test"
	@echo "  clear-mempool- Clear old buggy MTXs from mempool (restarts Hardhat)"
	@echo "  clean        - Clean logs and temporary files"

# =============================================================================
# Setup and Dependencies
# =============================================================================

setup:
	@echo "Installing Python dependencies..."
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	@echo "Installing Node.js dependencies..."
	cd $(BLOCKCHAIN_DIR) && npm install
	@echo "Creating logs directory..."
	mkdir -p $(LOGS_DIR)
	@echo "Setup complete! Copy env.example to .env and configure as needed."

# =============================================================================
# Development Environment
# =============================================================================

dev-up:
	@echo "Starting development environment..."
	@if [ ! -f .env ]; then \
		echo "⚠️  .env file not found. Copy env.example to .env first."; \
		exit 1; \
	fi
	@$(SCRIPTS_DIR)/dev_up.sh

dev-down:
	@echo "Stopping development environment..."
	@$(SCRIPTS_DIR)/dev_down.sh

dev-status:
	@echo "=== Development Services Status ==="
	@echo "IPFS daemon:"
	@if pgrep -f "ipfs daemon" > /dev/null; then \
		echo "  ✅ Running (PID: $$(pgrep -f 'ipfs daemon'))"; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo "Hardhat node:"
	@if pgrep -f "hardhat node" > /dev/null; then \
		echo "  ✅ Running (PID: $$(pgrep -f 'hardhat node'))"; \
	else \
		echo "  ❌ Not running"; \
	fi
	@echo "Checking connectivity..."
	@if curl -s http://127.0.0.1:8545 > /dev/null 2>&1; then \
		echo "  ✅ Hardhat RPC responsive"; \
	else \
		echo "  ❌ Hardhat RPC not responsive"; \
	fi
	@if curl -s http://127.0.0.1:5001/api/v0/version > /dev/null 2>&1; then \
		echo "  ✅ IPFS API responsive"; \
	else \
		echo "  ❌ IPFS API not responsive"; \
	fi

# =============================================================================
# Individual Services
# =============================================================================

chain:
	@echo "Starting Hardhat node..."
	cd $(BLOCKCHAIN_DIR) && npx hardhat node

deploy:
	@echo "Compiling and deploying contracts..."
	cd $(BLOCKCHAIN_DIR) && npx hardhat compile && npx hardhat deploy --network localhost

trainer:
	@echo "Starting D-PoDL trainer..."
	$(PYTHON) -m dpodl_core.trainer

# =============================================================================
# Logging and Monitoring
# =============================================================================

logs-ipfs:
	@if [ -f $(LOGS_DIR)/ipfs.log ]; then \
		tail -f $(LOGS_DIR)/ipfs.log; \
	else \
		echo "IPFS log file not found. Is IPFS running in background mode?"; \
	fi

logs-hardhat:
	@if [ -f $(LOGS_DIR)/hardhat.log ]; then \
		tail -f $(LOGS_DIR)/hardhat.log; \
	else \
		echo "Hardhat log file not found. Is Hardhat running in background mode?"; \
	fi

logs-all:
	@echo "Following all service logs (Ctrl+C to stop)..."
	@if [ -f $(LOGS_DIR)/ipfs.log ] && [ -f $(LOGS_DIR)/hardhat.log ]; then \
		tail -f $(LOGS_DIR)/*.log; \
	else \
		echo "Some log files not found. Run 'make dev-status' to check services."; \
	fi

# =============================================================================
# Testing
# =============================================================================

test:
	@echo "Running Python tests..."
	pytest -q
	@echo "Running Solidity tests..."
	cd $(BLOCKCHAIN_DIR) && npx hardhat test

test-e2e:
	@echo "Running end-to-end scenario test..."
	$(PYTHON) scripts/test_mtx_processing_e2e.py

# =============================================================================
# Cleanup
# =============================================================================

clean:
	@echo "Cleaning up logs and temporary files..."
	rm -f $(LOGS_DIR)/*.log
	rm -rf $(LOGS_DIR)
	mkdir -p $(LOGS_DIR)
	@echo "Cleanup complete."

clear-mempool:
	@echo "Clearing old buggy MTXs from mempool..."
	./scripts/clear_mempool.sh
