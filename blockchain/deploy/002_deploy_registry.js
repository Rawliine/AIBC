// blockchain/deploy/002_deploy_registry.js
const { network, ethers } = require("hardhat");
const { verify } = require("../utils/verify");
const {
    developmentChains, 
    initialT1Threshold, 
    initialAccuracyThresholdBPS, 
    initialBlockRewardAmount, 
    initialMinTrainingSteps, 
    initialMaxTrainingSteps, 
    initialMinAccuracyImprovementBPS, 
    initialMinStepImprovement,
    initialReferenceRewardShareBPS,
    // Import new config values
    initialGenesisModelStateCID, 
    initialGenesisDpodlCheckpointCID,
    initialMtxRewardAmount 
} = require("../helper-hardhat-config");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { deploy, log, get } = deployments;
    const { registryOwner, deployer } = await getNamedAccounts(); // Added deployer

    log("----------------------------------------------------");
    log("Deploying ModelRegistry...");

    const dpdlTokenDeployment = await get("DPoDLToken"); // Get DPoDLToken deployment details
    const tokenAddress = dpdlTokenDeployment.address;

    // Ensure helper-hardhat-config.js provides these values.
    // If any are undefined, the deployment might fail or use an unintended default from contract if not required by constructor.
    if (initialGenesisModelStateCID === undefined || initialGenesisDpodlCheckpointCID === undefined || initialMtxRewardAmount === undefined) {
        log("One or more required ModelRegistry constructor arguments (genesis CIDs, MTX reward) are undefined in helper-hardhat-config.js");
        log("Please define initialGenesisModelStateCID, initialGenesisDpodlCheckpointCID, and initialMtxRewardAmount in helper-hardhat-config.js");
        throw new Error("Missing ModelRegistry constructor arguments in helper configuration.");
    }

    const args = [
        initialT1Threshold,
        initialAccuracyThresholdBPS,
        initialBlockRewardAmount,
        initialMinTrainingSteps,
        initialMaxTrainingSteps,
        initialMinAccuracyImprovementBPS,
        initialMinStepImprovement,
        initialReferenceRewardShareBPS,
        tokenAddress,
        registryOwner, 
        initialGenesisModelStateCID,      
        initialGenesisDpodlCheckpointCID, 
        initialMtxRewardAmount            
    ];

    const modelRegistryDeployment = await deploy("ModelRegistry", {
        from: registryOwner, 
        args: args,
        log: true,
        waitConfirmations: network.config.blockConfirmations || 1, 
    });

    log(`ModelRegistry deployed at ${modelRegistryDeployment.address} (Owner: ${registryOwner})`);
    
    // Grant MINTER_ROLE to ModelRegistry contract from DPoDLToken
    log("Granting MINTER_ROLE to ModelRegistry from DPoDLToken...");
    try {
        const deployerSigner = await ethers.getSigner(deployer); // Get Signer for deployer address
        const dpdlTokenContract = await ethers.getContractAt("DPoDLToken", tokenAddress, deployerSigner); // Use deployerSigner
        const minterRole = await dpdlTokenContract.MINTER_ROLE(); // Fetch the role bytes32 value
        const txGrantRole = await dpdlTokenContract.grantRole(minterRole, modelRegistryDeployment.address);
        await txGrantRole.wait(1);
        log(`MINTER_ROLE granted to ModelRegistry (${modelRegistryDeployment.address}) on DPoDLToken (${tokenAddress}).`);
    } catch (error) {
        log(`Error granting MINTER_ROLE to ModelRegistry: ${error.message}`);
        log("Ensure the 'deployer' account has DEFAULT_ADMIN_ROLE on DPoDLToken and DPoDLToken has MINTER_ROLE defined.");
    }

    log("----------------------------------------------------");

    if (!developmentChains.includes(network.name) && process.env.ETHERSCAN_API_KEY) {
        log("Verifying ModelRegistry on Etherscan...");
        await verify(modelRegistryDeployment.address, args);
        log("ModelRegistry verified!");
        log("----------------------------------------------------");
    }
};

module.exports.dependencies = ["token"];
module.exports.tags = ["all", "registry"]; 