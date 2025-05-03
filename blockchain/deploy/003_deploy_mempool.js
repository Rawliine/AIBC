// blockchain/deploy/003_deploy_mempool.js
const { network } = require("hardhat");
const { verify } = require("../utils/verify");
const { developmentChains } = require("../helper-hardhat-config");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { deploy, log } = deployments;
    const { mempoolOwner } = await getNamedAccounts();

    log("----------------------------------------------------");
    log("Deploying MTXMempool...");

    const args = [mempoolOwner]; // Constructor expects initial owner address

    const mtxMempool = await deploy("MTXMempool", {
        from: mempoolOwner, // Deploy from the owner's account
        args: args,
        log: true,
        // waitConfirmations: network.config.blockConfirmations || 1,
    });

    log(`MTXMempool deployed at ${mtxMempool.address} (Owner: ${mempoolOwner})`);
    log("----------------------------------------------------");

    // Verification
    if (!developmentChains.includes(network.name) && process.env.ETHERSCAN_API_KEY) {
        log("Verifying MTXMempool on Etherscan...");
        await verify(mtxMempool.address, args);
        log("MTXMempool verified!");
        log("----------------------------------------------------");
    }
};

module.exports.tags = ["all", "mempool"]; 