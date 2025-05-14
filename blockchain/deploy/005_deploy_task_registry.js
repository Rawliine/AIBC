const { network } = require("hardhat");
const { verify } = require("../utils/verify");
const { developmentChains } = require("../helper-hardhat-config");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { deploy, log } = deployments;
    // Use deployer as the initial owner for simplicity, can be changed later
    const { deployer } = await getNamedAccounts(); 

    log("----------------------------------------------------");
    log("Deploying TaskRegistry...");

    const args = [deployer]; // Constructor expects initial owner address

    const taskRegistry = await deploy("TaskRegistry", {
        from: deployer, // Deploy from the owner's account
        args: args,
        log: true,
        waitConfirmations: network.config.blockConfirmations || 1,
    });

    log(`TaskRegistry deployed at ${taskRegistry.address} (Owner: ${deployer})`);
    log("----------------------------------------------------");

    // Verification on testnets/mainnet
    if (!developmentChains.includes(network.name) && process.env.ETHERSCAN_API_KEY) {
        log("Verifying TaskRegistry on Etherscan...");
        await verify(taskRegistry.address, args);
        log("TaskRegistry verified!");
        log("----------------------------------------------------");
    }
};

module.exports.tags = ["all", "taskregistry"]; 