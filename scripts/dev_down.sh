#!/bin/bash

# =============================================================================
# Development Environment Shutdown Script
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

stop_service() {
    local service_name=$1
    local process_pattern=$2
    
    local pids=$(pgrep -f "$process_pattern" || true)
    
    if [ -z "$pids" ]; then
        print_status "$service_name is not running"
        return 0
    fi
    
    print_status "Stopping $service_name (PIDs: $pids)..."
    
    # Try graceful shutdown first
    for pid in $pids; do
        if kill -TERM $pid 2>/dev/null; then
            print_status "Sent SIGTERM to $service_name (PID: $pid)"
        fi
    done
    
    # Wait a few seconds for graceful shutdown
    sleep 3
    
    # Force kill if still running
    local remaining_pids=$(pgrep -f "$process_pattern" || true)
    if [ -n "$remaining_pids" ]; then
        print_warning "Force killing $service_name (PIDs: $remaining_pids)..."
        for pid in $remaining_pids; do
            kill -KILL $pid 2>/dev/null || true
        done
        sleep 1
    fi
    
    # Verify shutdown
    local final_pids=$(pgrep -f "$process_pattern" || true)
    if [ -z "$final_pids" ]; then
        print_success "$service_name stopped successfully"
    else
        print_error "Failed to stop $service_name (PIDs still running: $final_pids)"
        return 1
    fi
}

# =============================================================================
# Main Script
# =============================================================================

print_status "Stopping AIBC development environment..."

# Stop Hardhat node
stop_service "Hardhat node" "hardhat node"

# Stop IPFS daemon
stop_service "IPFS daemon" "ipfs daemon"

# Clean up any Ray processes (if running)
if pgrep -f "ray" > /dev/null; then
    print_status "Stopping Ray processes..."
    pkill -f "ray" || true
    sleep 2
fi

# Optional: Clean up log files (commented out by default to preserve logs)
# print_status "Cleaning up log files..."
# rm -f logs/*.log

print_status ""
print_success "Development environment stopped!"
print_status ""
print_status "Log files preserved in logs/ directory"
print_status "To clean logs, run: make clean"
print_status ""
print_status "To restart the environment, run: make dev-up"
