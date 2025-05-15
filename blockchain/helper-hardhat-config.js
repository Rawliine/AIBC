// blockchain/helper-hardhat-config.js
const { ethers } = require("hardhat");

// Define networks considered for local development/testing
const developmentChains = ["hardhat", "localhost"];

// Define initial ModelRegistry parameters (can be moved to network-specific config later)
const initialT1Threshold = "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000";
const initialAccuracyThresholdBPS = 8500; // 85.00%
// Handle ethers v5 vs v6 compatibility
const parseEther = (value) => {
  // Check if we're using ethers v6 or v5
  if (ethers.parseEther) {
    // ethers v6
    return ethers.parseEther(value);
  } else if (ethers.utils && ethers.utils.parseEther) {
    // ethers v5
    return ethers.utils.parseEther(value);
  } else {
    // Fallback to BigNumber for extreme cases
    return ethers.BigNumber.from(value).mul(ethers.BigNumber.from(10).pow(18));
  }
};
const initialBlockRewardAmount = parseEther("100"); // 100 DPDL tokens per block
const initialMinTrainingSteps = 100;      // Minimum training steps required
const initialMaxTrainingSteps = 10000;    // Maximum training steps allowed
const initialMinAccuracyImprovementBPS = 100; // Require at least 1% accuracy improvement
const initialMinStepImprovement = 50;     // Require at least 50 additional training steps
const initialReferenceRewardShareBPS = 2000; // Example: 20% reward share for reference proposer

// New parameters for ModelRegistry constructor
const initialGenesisModelStateCID = "Qm__GENESIS_MODEL_STATE_CID_CONFIGURABLE__"; // Replace with actual CID for real deployments
const initialGenesisDpodlCheckpointCID = "Qm__GENESIS_DPODL_CHECKPOINT_CID_CONFIGURABLE__"; // Can be empty: "" if no DPoDL checkpoint for genesis
const initialMtxRewardAmount = parseEther("50"); // 50 DPDL tokens for a processed MTX

module.exports = {
    developmentChains,
    initialT1Threshold,
    initialAccuracyThresholdBPS,
    initialBlockRewardAmount,
    initialMinTrainingSteps,
    initialMaxTrainingSteps,
    initialMinAccuracyImprovementBPS,
    initialMinStepImprovement,
    initialReferenceRewardShareBPS,
    initialGenesisModelStateCID,      // Export new param
    initialGenesisDpodlCheckpointCID, // Export new param
    initialMtxRewardAmount,           // Export new param
    31337: { // Hardhat network
        // Only add values here if they should override the common defaults
    },
    1: { // Ethereum mainnet
        // Production values would go here
        // initialT1Threshold: "harder_value_for_production",
        // initialGenesisModelStateCID: "QmActualMainnetGenesisModel",
        // initialMtxRewardAmount: parseEther("10"),
    },
    // Add more networks as needed
}; 