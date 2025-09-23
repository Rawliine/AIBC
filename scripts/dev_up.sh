#!/bin/bash

# =============================================================================
# Development Environment Startup Script
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOGS_DIR="logs"
IPFS_LOG="$LOGS_DIR/ipfs.log"
HARDHAT_LOG="$LOGS_DIR/hardhat.log"
BLOCKCHAIN_DIR="blockchain"
MAX_RETRIES=30
RETRY_DELAY=1

# Functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependency() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed or not in PATH"
        exit 1
    fi
}

wait_for_service() {
    local url=$1
    local service_name=$2
    local retries=0
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s $url > /dev/null 2>&1; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        sleep $RETRY_DELAY
        retries=$((retries + 1))
        
        if [ $((retries % 10)) -eq 0 ]; then
            print_status "Still waiting for $service_name... ($retries/$MAX_RETRIES)"
        fi
    done
    
    print_error "$service_name failed to start within $MAX_RETRIES seconds"
    return 1
}

cleanup_on_exit() {
    print_warning "Received interrupt signal. Cleaning up..."
    ./scripts/dev_down.sh
    exit 130
}

# =============================================================================
# Main Script
# =============================================================================

print_status "Starting AIBC development environment..."

# Set up signal handling
trap cleanup_on_exit INT TERM

# Check dependencies
print_status "Checking dependencies..."
check_dependency "ipfs"
check_dependency "node"
check_dependency "npx"
check_dependency "curl"

# Create logs directory
mkdir -p $LOGS_DIR

# Check if services are already running
if pgrep -f "ipfs daemon" > /dev/null; then
    print_warning "IPFS daemon is already running"
else
    # Initialize IPFS if needed
    if [ ! -d ~/.ipfs ]; then
        print_status "Initializing IPFS..."
        ipfs init
    fi
    
    # Start IPFS daemon
    print_status "Starting IPFS daemon..."
    nohup ipfs daemon > $IPFS_LOG 2>&1 & disown
    
    # Wait for IPFS to be ready
    if ! wait_for_service "http://127.0.0.1:5001/api/v0/version" "IPFS"; then
        print_error "Failed to start IPFS daemon"
        exit 1
    fi
fi

if pgrep -f "hardhat node" > /dev/null; then
    print_warning "Hardhat node is already running"
else
    # Start Hardhat node
    print_status "Starting Hardhat node..."
    cd $BLOCKCHAIN_DIR
    nohup npx hardhat node > ../$HARDHAT_LOG 2>&1 & disown
    cd ..
    
    # Wait for Hardhat to be ready
    if ! wait_for_service "http://127.0.0.1:8545" "Hardhat node"; then
        print_error "Failed to start Hardhat node"
        exit 1
    fi
fi

# Compile and deploy contracts
print_status "Compiling and deploying contracts..."
cd $BLOCKCHAIN_DIR

# Compile contracts
print_status "Compiling contracts..."
if ! npx hardhat compile; then
    print_error "Contract compilation failed"
    cd ..
    exit 1
fi

# Deploy contracts
print_status "Deploying contracts to localhost..."
if ! npx hardhat deploy --network localhost; then
    print_error "Contract deployment failed"
    cd ..
    exit 1
fi

cd ..

print_success "Development environment is ready!"
print_status ""
print_status "Services running:"
print_status "  • IPFS daemon: http://127.0.0.1:5001"
print_status "  • Hardhat node: http://127.0.0.1:8545"
print_status ""
print_status "Logs available at:"
print_status "  • IPFS: $IPFS_LOG"
print_status "  • Hardhat: $HARDHAT_LOG"
print_status ""
print_status "Next steps:"
print_status "  • Run 'make trainer' to start the D-PoDL trainer"
print_status "  • Run 'make logs-all' to follow service logs"
print_status "  • Run 'make dev-down' to stop all services"
print_status ""
print_success "Ready to develop! 🚀"
