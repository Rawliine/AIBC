const { network } = require("hardhat");
const { verify } = require("../utils/verify"); // Helper for Etherscan verification
const { developmentChains } = require("../helper-hardhat-config"); // Network types helper

// Using module.exports syntax for hardhat-deploy
module.exports = async ({ getNamedAccounts, deployments }) => {
    const { deploy, log } = deployments;
    const { deployer } = await getNamedAccounts(); // Get the deployer account from namedAccounts config
    const chainId = network.config.chainId;

    log("----------------------------------------------------");
    log("Deploying DPoDLToken...");

    // Define constructor arguments
    // Remember ERC20 takes initialSupply which needs decimal adjustment
    // 1,000,000 tokens with 18 decimals
    const initialSupply = 1000000n; // Supply *before* decimal adjustment

    const args = [initialSupply]; // Constructor expects supply before decimal adjustment

    const dpdlToken = await deploy("DPoDLToken", {
        from: deployer,
        args: args, // Pass constructor arguments
        log: true, // Log deployment info (address, gas cost, etc.)
        // waitConfirmations: network.config.blockConfirmations || 1, // Optional: wait for X confirmations
    });

    log(`DPoDLToken deployed at ${dpdlToken.address}`);
    log("----------------------------------------------------");

    // --- Verification --- (Optional: Only run on testnets/mainnet with API key)
    if (!developmentChains.includes(network.name) && process.env.ETHERSCAN_API_KEY) {
        log("Verifying DPoDLToken on Etherscan...");
        await verify(dpdlToken.address, args);
        log("DPoDLToken verified!");
        log("----------------------------------------------------");
    }
};

// Add tags for selective deployment
module.exports.tags = ["all", "token"]; 