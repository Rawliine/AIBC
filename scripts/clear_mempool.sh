#!/bin/bash

# Script to clear old buggy MTXs from mempool by restarting Hardhat node
# This is needed because old MTXs were signed with wrong keys before the EIP-712 fix

set -e

echo "🧹 Clearing old MTXs from mempool by restarting Hardhat node..."

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Stop Hardhat node if running
echo "🛑 Stopping Hardhat node..."
make dev-down || echo "Hardhat node was not running"

# Wait a moment for cleanup
sleep 2

# Start fresh Hardhat node
echo "🚀 Starting fresh Hardhat node..."
make dev-up

echo "✅ Mempool cleared! Old buggy MTXs are gone."
echo "💡 Note: This restarts the entire blockchain, so any previous state is lost."
