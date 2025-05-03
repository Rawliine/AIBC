// blockchain/deploy/004_configure_roles.js
const { ethers } = require("hardhat");

module.exports = async ({ getNamedAccounts, deployments }) => {
    const { log, get } = deployments;
    const { deployer } = await getNamedAccounts(); // Account with admin role on token

    log("----------------------------------------------------");
    log("Configuring contract roles...");

    // Get deployed contracts
    // We need the signer to interact with the token contract
    const deployerSigner = await ethers.getSigner(deployer);
    const dpdlTokenDeployment = await get("DPoDLToken");
    const dpdlToken = await ethers.getContractAt("DPoDLToken", dpdlTokenDeployment.address, deployerSigner);

    const modelRegistryDeployment = await get("ModelRegistry");
    const modelRegistryAddress = modelRegistryDeployment.address;

    // Get the MINTER_ROLE hash
    const minterRole = await dpdlToken.MINTER_ROLE();

    // Check if registry already has the role
    const hasRole = await dpdlToken.hasRole(minterRole, modelRegistryAddress);

    if (!hasRole) {
        // Grant MINTER_ROLE to ModelRegistry contract
        log(`Granting MINTER_ROLE to ModelRegistry (${modelRegistryAddress})...`);
        const tx = await dpdlToken.grantRole(minterRole, modelRegistryAddress);
        await tx.wait(1); // Wait for 1 confirmation
        log(`MINTER_ROLE granted to ModelRegistry!`);
    } else {
        log(`ModelRegistry (${modelRegistryAddress}) already has MINTER_ROLE.`);
    }

    log("Role configuration complete.");
    log("----------------------------------------------------");
};

// Define dependencies: Roles can only be configured after token and registry are deployed
module.exports.dependencies = ["token", "registry"];
module.exports.tags = ["all", "configure"]; 