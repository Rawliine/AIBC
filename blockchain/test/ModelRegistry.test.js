const { expect } = require("chai");
const { ethers } = require("hardhat");

// Helper function to convert token amounts to the smallest unit (considering 18 decimals)
const toWei = (value) => ethers.parseEther(value.toString());

// Helper function to convert token amounts from the smallest unit
const fromWei = (value) => ethers.formatEther(typeof value === "string" ? value : value.toString());

describe("ModelRegistry", function () {
    let DPoDLToken, token;
    let ModelRegistry, registry;
    let owner, proposer1, proposer2, addrs;

    // Initial parameters for the registry
    const initialT1Threshold = 50000n; // Example threshold (BigInt)
    const initialAccuracyThresholdBPS = 8500n; // 85.00% (BigInt)
    const initialBlockRewardAmount = toWei(100); // 100 DPDL tokens (BigInt)
    const initialTokenSupply = 1000000n; // Supply for the token contract

    beforeEach(async function () {
        // Get signers
        [owner, proposer1, proposer2, ...addrs] = await ethers.getSigners();

        // Deploy the DPoDLToken contract first
        DPoDLToken = await ethers.getContractFactory("DPoDLToken");
        token = await DPoDLToken.deploy(initialTokenSupply);
        await token.waitForDeployment();
        const tokenAddress = await token.getAddress();

        // Deploy the ModelRegistry contract
        ModelRegistry = await ethers.getContractFactory("ModelRegistry");
        registry = await ModelRegistry.deploy(
            initialT1Threshold,
            initialAccuracyThresholdBPS,
            initialBlockRewardAmount,
            tokenAddress,
            owner.address // Explicitly set the owner
        );
        await registry.waitForDeployment();

        // **Important:** Grant minting role/permission to the registry contract
        // This step is crucial for the reward mechanism to work.
        // We assume the DPoDLToken's owner (deployer) can grant minting rights.
        // In DPoDLToken, the owner is implicitly the minter.
        // No explicit role needed if using the default Ownable mint function.
        // If DPoDLToken used specific roles (e.g., MINTER_ROLE), we'd grant it here:
        // const MINTER_ROLE = await token.MINTER_ROLE(); // Assuming it exists
        // await token.grantRole(MINTER_ROLE, await registry.getAddress());
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await registry.owner()).to.equal(owner.address);
        });

        it("Should set the correct initial parameters", async function () {
            expect(await registry.t1Threshold()).to.equal(initialT1Threshold);
            expect(await registry.tAccuracyThresholdBPS()).to.equal(initialAccuracyThresholdBPS);
            expect(await registry.blockRewardAmount()).to.equal(initialBlockRewardAmount);
        });

        it("Should set the correct DPDL token address", async function () {
            expect(await registry.dpdlToken()).to.equal(await token.getAddress());
        });

        it("Should initialize currentBlockHeight to 0", async function () {
            expect(await registry.currentBlockHeight()).to.equal(0);
        });

        it("Should emit ParameterUpdated events on deployment", async function () {
            const registryAddress = await registry.getAddress();
            const deployTx = registry.deploymentTransaction();
            // We need to get the transaction receipt to check events
            const receipt = await deployTx.wait();

            // Check for ParameterUpdated events (adjust expected values as needed)
            await expect(deployTx)
                .to.emit(registry, "ParameterUpdated").withArgs("t1Threshold", initialT1Threshold)
                .and.to.emit(registry, "ParameterUpdated").withArgs("tAccuracyThresholdBPS", initialAccuracyThresholdBPS)
                .and.to.emit(registry, "ParameterUpdated").withArgs("blockRewardAmount", initialBlockRewardAmount)
                .and.to.emit(registry, "ParameterUpdated").withArgs("dpdlToken", BigInt(await token.getAddress())); // Compare BigInt representation of address
        });

        it("Should fail deployment with zero token address", async function () {
            await expect(ModelRegistry.deploy(
                initialT1Threshold,
                initialAccuracyThresholdBPS,
                initialBlockRewardAmount,
                ethers.ZeroAddress, // Use ZeroAddress constant
                owner.address
            )).to.be.revertedWithCustomError(ModelRegistry, "ZeroAddress");
        });

        it("Should fail deployment with zero owner address", async function () {
             await expect(ModelRegistry.deploy(
                initialT1Threshold,
                initialAccuracyThresholdBPS,
                initialBlockRewardAmount,
                await token.getAddress(),
                ethers.ZeroAddress // Use ZeroAddress constant
            )).to.be.revertedWithCustomError(ModelRegistry, "OwnableInvalidOwner") // Standard Ownable error
                .withArgs(ethers.ZeroAddress);
        });

         it("Should fail deployment with invalid accuracy BPS", async function () {
            await expect(ModelRegistry.deploy(
                initialT1Threshold,
                10001n, // Invalid BPS > 10000
                initialBlockRewardAmount,
                await token.getAddress(),
                owner.address
            )).to.be.revertedWith("Accuracy BPS cannot exceed 10000");
        });
    });

    // --- Add more describe blocks for other functions (submitBlock, parameter updates, views) ---

    describe("Block Submission", function () {
       // Tests for submitBlock success, failures (thresholds, reference CID), rewards
       it("Should allow submitting the first valid block (genesis reference)", async function() {
           const modelCID = "QmValidCIDForFirstBlock"; // Example valid IPFS CID
           const t1Hash = "0x" + "0".repeat(63) + "1"; // Example hash below threshold
           const accuracyBPS = 9000n; // 90.00% > initial 85.00%
           const genesisReferenceCID = ""; // First block references empty string (current contract logic)
           const steps = 1000n; // Placeholder steps value

           await expect(registry.connect(proposer1).submitBlock(
               modelCID,
               t1Hash,
               accuracyBPS,
               steps,
               genesisReferenceCID
           ))
               .to.emit(registry, "ModelAccepted")
               .withArgs(1, modelCID, accuracyBPS, t1Hash, genesisReferenceCID, proposer1.address);

           expect(await registry.currentBlockHeight()).to.equal(1);
           expect(await registry.getCurrentReferenceModel()).to.equal(modelCID);

           const blockDetails = await registry.getBlockDetails(1);
           expect(blockDetails.proposer).to.equal(proposer1.address);
           expect(blockDetails.modelCID).to.equal(modelCID);
           expect(blockDetails.t1Hash).to.equal(t1Hash);
           expect(blockDetails.accuracyBPS).to.equal(accuracyBPS);
           expect(blockDetails.referenceModelCID).to.equal(genesisReferenceCID);

           expect(await registry.getBlockHeightForCID(modelCID)).to.equal(1);
       });

       it("Should reward the proposer with tokens upon successful submission", async function() {
           const modelCID = "QmValidCIDForRewardTest";
           const t1Hash = "0x" + "0".repeat(63) + "2";
           const accuracyBPS = 9100n; // 91.00% > initial 85.00%
           const genesisReferenceCID = ethers.ZeroHash;
           const steps = 1000n; // Placeholder steps value

           const initialBalance = await token.balanceOf(proposer1.address);
           const rewardAmount = await registry.blockRewardAmount();

           await registry.connect(proposer1).submitBlock(
               modelCID,
               t1Hash,
               accuracyBPS,
               steps,
               genesisReferenceCID
           );

           const finalBalance = await token.balanceOf(proposer1.address);

           expect(finalBalance).to.equal(initialBalance + rewardAmount);
       });

       it("Should fail if reference model CID doesn't match current head", async function() {
            // TODO
       });

       it("Should fail if accuracy is below threshold", async function() {
           // TODO
       });

       it("Should fail if T1 hash is not below threshold", async function() {
           // TODO
       });

       // etc.
    });

    describe("Parameter Updates", function () {
        // Tests for setT1Threshold, setTAccuracyThresholdBPS, setBlockRewardAmount, setTokenAddress
        // Including owner checks and event emissions
        it("Should allow owner to update T1 threshold", async function() {
            // TODO
        });
         it("Should prevent non-owner from updating T1 threshold", async function() {
            // TODO
        });
        // etc.
    });

     describe("View Functions", function () {
        // Tests for getCurrentReferenceModel, getBlockDetails, getBlockHeightForCID
         it("Should return correct reference model CID", async function() {
            // TODO
        });
         // etc.
     });

}); 