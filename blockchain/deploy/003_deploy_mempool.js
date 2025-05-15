// blockchain/deploy/003_deploy_mempool.js
const { network, ethers } = require("hardhat");
const { verify } = require("../utils/verify");
const { developmentChains } = require("../helper-hardhat-config");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { deploy, log, get } = deployments;
    const { mempoolOwner } = await getNamedAccounts();

    log("----------------------------------------------------");
    log("Deploying MTXMempool...");

    const args = [mempoolOwner]; // Constructor expects initial owner address

    const mtxMempoolDeployment = await deploy("MTXMempool", {
        from: mempoolOwner,
        args: args,
        log: true,
        waitConfirmations: network.config.blockConfirmations || 1,
    });

    log(`MTXMempool deployed at ${mtxMempoolDeployment.address} (Owner: ${mempoolOwner})`);

    // REMOVED: Set ModelRegistry contract address in MTXMempool - This will be done in a separate script
    // log("Fetching ModelRegistry contract to link with MTXMempool...");
    // try {
    //     const modelRegistry = await get("ModelRegistry");
    //     if (modelRegistry && modelRegistry.address) {
    //         log(`ModelRegistry found at ${modelRegistry.address}. Setting it in MTXMempool...`);
    //         const mtxMempoolContract = await ethers.getContractAt("MTXMempool", mtxMempoolDeployment.address, mempoolOwner);
    //         const tx = await mtxMempoolContract.setModelRegistryContract(modelRegistry.address);
    //         await tx.wait(1);
    //         log(`ModelRegistry address (${modelRegistry.address}) set in MTXMempool.`);
    //     } else {
    //         log("ModelRegistry contract not found or address missing. Skipping linking in MTXMempool.");
    //     }
    // } catch (error) {
    //     log("Error fetching ModelRegistry or linking to MTXMempool: ", error.message);
    //     log("Ensure ModelRegistry is deployed correctly and its deployment is tagged as 'registry'.");
    // }
    log("----------------------------------------------------");

    // Verification
    if (!developmentChains.includes(network.name) && process.env.ETHERSCAN_API_KEY) {
        log("Verifying MTXMempool on Etherscan...");
        await verify(mtxMempoolDeployment.address, args);
        log("MTXMempool verified!");
        log("----------------------------------------------------");
    }
};

module.exports.dependencies = []; // REMOVED dependency on "registry"
module.exports.tags = ["all", "mempool"]; 