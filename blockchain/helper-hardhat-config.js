// blockchain/helper-hardhat-config.js
const { ethers } = require("hardhat");

// Define networks considered for local development/testing
const developmentChains = ["hardhat", "localhost"];

// Define initial ModelRegistry parameters (can be moved to network-specific config later)
const initialT1Threshold = 50000n;
const initialAccuracyThresholdBPS = 8500n; // 85.00%
const initialBlockRewardAmount = ethers.parseEther("100"); // 100 DPDL (requires ethers)

module.exports = {
    developmentChains,
    initialT1Threshold,
    initialAccuracyThresholdBPS,
    initialBlockRewardAmount,
}; 