const { network, ethers } = require("hardhat");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { log, get } = deployments;
    const { registryOwner, mempoolOwner } = await getNamedAccounts();

    // Fetch deployer for token operations, assuming deployer has DEFAULT_ADMIN_ROLE on token
    // This 'deployer' should be the account that deployed DPoDLToken and thus has DEFAULT_ADMIN_ROLE
    const { deployer } = await getNamedAccounts(); 

    log("----------------------------------------------------");
    log("Linking ModelRegistry and MTXMempool contracts...");

    // Get deployed contracts
    const modelRegistryDeployment = await get("ModelRegistry");
    const mtxMempoolDeployment = await get("MTXMempool");
    const dpodlTokenDeployment = await get("DPoDLToken"); // Get DPoDLToken deployment

    log(`ModelRegistry found at ${modelRegistryDeployment.address}`);
    log(`MTXMempool found at ${mtxMempoolDeployment.address}`);
    log(`DPoDLToken found at ${dpodlTokenDeployment.address}`); // Log token address

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

        // Grant MINTER_ROLE to ModelRegistry on DPoDLToken
        // Ensure 'deployer' is the account that deployed DPoDLToken and has DEFAULT_ADMIN_ROLE
        const deployerSigner = await ethers.getSigner(deployer);
        const dpodlToken = await ethers.getContractAt("DPoDLToken", dpodlTokenDeployment.address, deployerSigner);
        
        const MINTER_ROLE = await dpodlToken.MINTER_ROLE(); // Get the role hash from the token contract
        log(`Granting MINTER_ROLE (${MINTER_ROLE}) to ModelRegistry (${modelRegistryDeployment.address}) on DPoDLToken (${dpodlTokenDeployment.address}) as ${deployer}...`);
        
        if (await dpodlToken.hasRole(MINTER_ROLE, modelRegistryDeployment.address)) {
            log(`ModelRegistry already has MINTER_ROLE.`);
        } else {
            const tx3 = await dpodlToken.grantRole(MINTER_ROLE, modelRegistryDeployment.address);
            await tx3.wait(1);
            log("MINTER_ROLE granted to ModelRegistry successfully.");
        }

    } catch (error) {
        log("Error linking ModelRegistry to MTXMempool or granting MINTER_ROLE: " + error.message);
        log("Ensure 'registryOwner' has ownership of ModelRegistry and 'deployer' has DEFAULT_ADMIN_ROLE on DPoDLToken.");
        throw error; // Re-throw to halt deployment if linking fails
    }

    log("----------------------------------------------------");
    log("Contract linking complete.");
    log("----------------------------------------------------");
};

module.exports.dependencies = ["registry", "mempool", "token"]; // Added "token" dependency
module.exports.tags = ["all", "linking"]; 