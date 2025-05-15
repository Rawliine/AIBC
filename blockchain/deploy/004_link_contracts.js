const { network, ethers } = require("hardhat");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { log, get } = deployments;
    const { registryOwner, mempoolOwner } = await getNamedAccounts();

    log("----------------------------------------------------");
    log("Linking ModelRegistry and MTXMempool contracts...");

    // Get deployed contracts
    const modelRegistryDeployment = await get("ModelRegistry");
    const mtxMempoolDeployment = await get("MTXMempool");

    log(`ModelRegistry found at ${modelRegistryDeployment.address}`);
    log(`MTXMempool found at ${mtxMempoolDeployment.address}`);

    // Link MTXMempool to ModelRegistry (MTXMempool.setModelRegistryContract)
    try {
        const mempoolOwnerSigner = await ethers.getSigner(mempoolOwner);
        const mtxMempoolContract = await ethers.getContractAt("MTXMempool", mtxMempoolDeployment.address, mempoolOwnerSigner);
        log(`Calling setModelRegistryContract(${modelRegistryDeployment.address}) on MTXMempool (${mtxMempoolDeployment.address}) as ${mempoolOwner}...`);
        const tx1 = await mtxMempoolContract.setModelRegistryContract(modelRegistryDeployment.address);
        await tx1.wait(1);
        log("MTXMempool linked to ModelRegistry successfully.");
    } catch (error) {
        log("Error linking MTXMempool to ModelRegistry: " + error.message);
        log("Ensure 'mempoolOwner' has ownership of MTXMempool and the contract interface is correct.");
        throw error; // Re-throw to halt deployment if linking fails
    }

    // Link ModelRegistry to MTXMempool (ModelRegistry.setMtxMempoolContract)
    try {
        const registryOwnerSigner = await ethers.getSigner(registryOwner);
        const modelRegistryContract = await ethers.getContractAt("ModelRegistry", modelRegistryDeployment.address, registryOwnerSigner);
        log(`Calling setMtxMempoolContract(${mtxMempoolDeployment.address}) on ModelRegistry (${modelRegistryDeployment.address}) as ${registryOwner}...`);
        const tx2 = await modelRegistryContract.setMtxMempoolContract(mtxMempoolDeployment.address);
        await tx2.wait(1);
        log("ModelRegistry linked to MTXMempool successfully.");
    } catch (error) {
        log("Error linking ModelRegistry to MTXMempool: " + error.message);
        log("Ensure 'registryOwner' has ownership of ModelRegistry and the contract interface is correct.");
        throw error; // Re-throw to halt deployment if linking fails
    }

    log("----------------------------------------------------");
    log("Contract linking complete.");
    log("----------------------------------------------------");
};

module.exports.dependencies = ["registry", "mempool"]; // Depends on both registry and mempool deployments
module.exports.tags = ["all", "linking"]; 