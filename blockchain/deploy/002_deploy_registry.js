// blockchain/deploy/002_deploy_registry.js
const { network, ethers } = require("hardhat");
const { verify } = require("../utils/verify");
const { developmentChains, initialT1Threshold, initialAccuracyThresholdBPS, initialBlockRewardAmount } = require("../helper-hardhat-config");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { deploy, log, get } = deployments;
    // Get the registryOwner account (defaults to deployer if not specified differently for the network)
    const { registryOwner } = await getNamedAccounts();

    log("----------------------------------------------------");
    log("Deploying ModelRegistry...");

    // Get the deployed DPoDLToken contract instance to pass its address
    const dpdlToken = await get("DPoDLToken");
    const tokenAddress = dpdlToken.address;

    // Use parameters from helper config
    const args = [
        initialT1Threshold,
        initialAccuracyThresholdBPS,
        initialBlockRewardAmount,
        tokenAddress,
        registryOwner, // Set the designated owner
    ];

    const modelRegistry = await deploy("ModelRegistry", {
        from: registryOwner, // Deploy from the owner's account
        args: args,
        log: true,
        // waitConfirmations: network.config.blockConfirmations || 1,
    });

    log(`ModelRegistry deployed at ${modelRegistry.address} (Owner: ${registryOwner})`);
    log("----------------------------------------------------");

    // Verification
    if (!developmentChains.includes(network.name) && process.env.ETHERSCAN_API_KEY) {
        log("Verifying ModelRegistry on Etherscan...");
        await verify(modelRegistry.address, args);
        log("ModelRegistry verified!");
        log("----------------------------------------------------");
    }
};

// Define dependency: ModelRegistry needs DPoDLToken deployed first
module.exports.dependencies = ["token"]; 
module.exports.tags = ["all", "registry"]; 