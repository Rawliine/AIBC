const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

// Helper function to convert token amounts to the smallest unit (considering 18 decimals)
const toWei = (value) => ethers.parseEther(value.toString());

// Helper function to convert token amounts from the smallest unit
const fromWei = (value) => ethers.formatEther(typeof value === "string" ? value : value.toString());

describe("ModelRegistry", function () {
    // Define the fixture for deploying contracts and setting up roles/ownership
    async function deployContractsAndTokenFixture() {
        // Get signers
        const [owner, proposer1, proposer2, referenceProposer, ...addrs] = await ethers.getSigners();

        // Deploy the DPoDLToken contract first
        const initialTokenSupply = 1000000n;
        const DPoDLToken = await ethers.getContractFactory("DPoDLToken");
        const token = await DPoDLToken.deploy(initialTokenSupply);
        await token.waitForDeployment();
        const tokenAddress = await token.getAddress();

        // Deploy the ModelRegistry contract
        const initialT1Threshold = 50000n; // Example threshold (BigInt)
        const initialAccuracyThresholdBPS = 8500n; // 85.00% (BigInt)
        const initialBlockRewardAmount = toWei(100); // 100 DPDL tokens (BigInt)
        const initialMinSteps = 100n;
        const initialMaxSteps = 10000n;
        const initialMinAccImprov = 100n; // 1%
        const initialMinStepImprov = 50n;
        const initialRefRewardShare = 2000n; // 20%

        const ModelRegistry = await ethers.getContractFactory("ModelRegistry");
        const registry = await ModelRegistry.deploy(
            initialT1Threshold,
            initialAccuracyThresholdBPS,
            initialBlockRewardAmount,
            initialMinSteps,
            initialMaxSteps,
            initialMinAccImprov,
            initialMinStepImprov,
            initialRefRewardShare,
            token.target, // _tokenAddress
            owner.address, // _initialOwner
            "QmGenesisModelStateCID", // _initialGenesisModelStateCID
            "QmGenesisDpodlCheckpointCID", // _initialGenesisDpodlCheckpointCID
            ethers.parseEther("10") // _initialMtxRewardAmount
        );
        await registry.waitForDeployment();

        // Grant MINTER_ROLE to the ModelRegistry contract from the owner account
        const MINTER_ROLE = await token.MINTER_ROLE();
        await token.connect(owner).grantRole(MINTER_ROLE, await registry.getAddress());

        // Return all necessary objects
        return { token, registry, owner, proposer1, proposer2, referenceProposer, addrs,
                 initialT1Threshold, initialAccuracyThresholdBPS, initialBlockRewardAmount,
                 initialMinSteps, initialMaxSteps, initialMinAccImprov, initialMinStepImprov,
                 initialRefRewardShare };
    }

    // Use beforeEach only to load the fixture for most tests
    let token, registry, owner, proposer1, proposer2, referenceProposer, addrs;
    let initialT1Threshold, initialAccuracyThresholdBPS, initialBlockRewardAmount;
    let initialMinSteps, initialMaxSteps, initialMinAccImprov, initialMinStepImprov, initialRefRewardShare;

    beforeEach(async function () {
        // Load the fixture defined above
        const fixtures = await loadFixture(deployContractsAndTokenFixture);
        token = fixtures.token;
        registry = fixtures.registry;
        owner = fixtures.owner;
        proposer1 = fixtures.proposer1;
        proposer2 = fixtures.proposer2;
        referenceProposer = fixtures.referenceProposer;
        addrs = fixtures.addrs;
        initialT1Threshold = fixtures.initialT1Threshold;
        initialAccuracyThresholdBPS = fixtures.initialAccuracyThresholdBPS;
        initialBlockRewardAmount = fixtures.initialBlockRewardAmount;
        initialMinSteps = fixtures.initialMinSteps;
        initialMaxSteps = fixtures.initialMaxSteps;
        initialMinAccImprov = fixtures.initialMinAccImprov;
        initialMinStepImprov = fixtures.initialMinStepImprov;
        initialRefRewardShare = fixtures.initialRefRewardShare;
    });

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            expect(await registry.owner()).to.equal(owner.address);
        });

        it("Should set the correct initial parameters", async function () {
            expect(await registry.t1Threshold()).to.equal(initialT1Threshold);
            expect(await registry.tAccuracyThresholdBPS()).to.equal(initialAccuracyThresholdBPS);
            expect(await registry.blockRewardAmount()).to.equal(initialBlockRewardAmount);
            expect(await registry.minTrainingSteps()).to.equal(initialMinSteps);
            expect(await registry.maxTrainingSteps()).to.equal(initialMaxSteps);
            expect(await registry.minAccuracyImprovementBPS()).to.equal(initialMinAccImprov);
            expect(await registry.minStepImprovement()).to.equal(initialMinStepImprov);
            expect(await registry.referenceRewardShareBPS()).to.equal(initialRefRewardShare);
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
                .and.to.emit(registry, "ParameterUpdated").withArgs("minTrainingSteps", initialMinSteps)
                .and.to.emit(registry, "ParameterUpdated").withArgs("maxTrainingSteps", initialMaxSteps)
                .and.to.emit(registry, "ParameterUpdated").withArgs("minAccuracyImprovementBPS", initialMinAccImprov)
                .and.to.emit(registry, "ParameterUpdated").withArgs("minStepImprovement", initialMinStepImprov)
                .and.to.emit(registry, "ParameterUpdated").withArgs("referenceRewardShareBPS", initialRefRewardShare)
                .and.to.emit(registry, "ParameterUpdated").withArgs("dpdlToken", BigInt(await token.getAddress())); // Compare BigInt representation of address
        });

        it("Should fail deployment with zero token address", async function () {
            const { initialT1Threshold, initialAccuracyThresholdBPS, initialBlockRewardAmount, owner } = await loadFixture(deployContractsAndTokenFixture);
            const ModelRegistry = await ethers.getContractFactory("ModelRegistry"); // Get factory here
            await expect(ModelRegistry.deploy(
                initialT1Threshold,
                initialAccuracyThresholdBPS,
                initialBlockRewardAmount,
                100n, 10000n, 100n, 50n, 2000n, // minSteps, maxSteps, minAccImprov, minStepImprov, refRewardShare
                ethers.ZeroAddress, // _tokenAddress (zero address)
                owner.address, // _initialOwner
                "QmGenesisModelStateCID", // _initialGenesisModelStateCID
                "QmGenesisDpodlCheckpointCID", // _initialGenesisDpodlCheckpointCID
                ethers.parseEther("10") // _initialMtxRewardAmount
            )).to.be.revertedWithCustomError(ModelRegistry, "ZeroAddress");
        });

        it("Should fail deployment with zero owner address", async function () {
            const { initialT1Threshold, initialAccuracyThresholdBPS, initialBlockRewardAmount, token, owner } = await loadFixture(deployContractsAndTokenFixture);
            const ModelRegistry = await ethers.getContractFactory("ModelRegistry"); // Get factory here
             await expect(ModelRegistry.deploy(
                initialT1Threshold,
                initialAccuracyThresholdBPS,
                initialBlockRewardAmount,
                100n, 10000n, 100n, 50n, 2000n, // minSteps, maxSteps, minAccImprov, minStepImprov, refRewardShare
                await token.getAddress(), // _tokenAddress
                ethers.ZeroAddress, // _initialOwner (zero address)
                "QmGenesisModelStateCID", // _initialGenesisModelStateCID
                "QmGenesisDpodlCheckpointCID", // _initialGenesisDpodlCheckpointCID
                ethers.parseEther("10") // _initialMtxRewardAmount
            )).to.be.revertedWithCustomError(ModelRegistry, "OwnableInvalidOwner") // Standard Ownable error
                .withArgs(ethers.ZeroAddress);
        });

         it("Should fail deployment with invalid accuracy BPS", async function () {
            const { initialT1Threshold, initialBlockRewardAmount, token, owner } = await loadFixture(deployContractsAndTokenFixture);
            const ModelRegistry = await ethers.getContractFactory("ModelRegistry"); // Get factory here
            await expect(ModelRegistry.deploy(
                initialT1Threshold,
                10001n, // Invalid BPS > 10000 (_initialTAccuracyThresholdBPS)
                initialBlockRewardAmount,
                100n, 10000n, 100n, 50n, 2000n, // minSteps, maxSteps, minAccImprov, minStepImprov, refRewardShare
                await token.getAddress(), // _tokenAddress
                owner.address, // _initialOwner
                "QmGenesisModelStateCID", // _initialGenesisModelStateCID
                "QmGenesisDpodlCheckpointCID", // _initialGenesisDpodlCheckpointCID
                ethers.parseEther("10") // _initialMtxRewardAmount
            )).to.be.revertedWith("Accuracy BPS cannot exceed 10000");
        });

        it("Should fail deployment with invalid reference reward share BPS", async function () {
            const { initialT1Threshold, initialAccuracyThresholdBPS, initialBlockRewardAmount, token, owner } = await loadFixture(deployContractsAndTokenFixture);
            const ModelRegistry = await ethers.getContractFactory("ModelRegistry");
            await expect(ModelRegistry.deploy(
                initialT1Threshold,
                initialAccuracyThresholdBPS,
                initialBlockRewardAmount,
                100n, 10000n, 100n, 50n,
                10001n, // Invalid ref share > 10000
                await token.getAddress(), // _tokenAddress
                owner.address, // _initialOwner
                "QmGenesisModelStateCID", // _initialGenesisModelStateCID
                "QmGenesisDpodlCheckpointCID", // _initialGenesisDpodlCheckpointCID
                ethers.parseEther("10") // _initialMtxRewardAmount
            )).to.be.revertedWith("Reference reward share BPS cannot exceed 10000");
        });
    });

    // --- Add more describe blocks for other functions (submitBlock, parameter updates, views) ---

    describe("Block Submission", function () {
       // Tests for submitBlock success, failures (thresholds, reference CID), rewards
       it("Should allow submitting the first valid block (genesis reference)", async function() {
           const modelCID = "testCID"; // Simpler CID string
           const t1Hash = "0x" + "0".repeat(63) + "1"; // Example hash below threshold
           const accuracyBPS = 9000n; // 90.00% > initial 85.00%
           const genesisReferenceCID = ""; // First block references empty string (current contract logic)
           const steps = 1000n; // Placeholder steps value

           await expect(registry.connect(proposer1).submitBlock(
               modelCID,                // _newModelStateCID
               "QmDpodlCheckpointCID",  // _newDpodlCheckpointCID 
               accuracyBPS,             // _accuracyBPS
               steps,                   // _steps
               t1Hash,                  // _postHash
               "QmGenesisDpodlCheckpointCID" // _referenceDpodlCheckpointCID (must match constructor value)
           ))
               .to.emit(registry, "ModelAccepted")
               .withArgs(
                   1,                     // blockHeight
                   modelCID,            // modelStateCID
                   "QmDpodlCheckpointCID", // dpodlCheckpointCID
                   accuracyBPS,         // accuracyBPS
                   t1Hash,              // postHash
                   "QmGenesisDpodlCheckpointCID", // referenceModelCID (must match constructor value)
                   proposer1.address,   // proposer
                   anyValue             // timestamp (ignore value)
               );

           // Check current block height first
           expect(await registry.currentBlockHeight()).to.equal(1);

           // Check details of the newly added block 1
           const blockDetails = await registry.getBlockDetails(1);
           // Check fields that seem to work first
           expect(blockDetails.proposer).to.equal(proposer1.address);
           expect(blockDetails.accuracyBPS).to.equal(accuracyBPS);
           expect(blockDetails.postHash).to.equal(t1Hash);
           expect(blockDetails.referenceModelCID).to.equal("QmGenesisDpodlCheckpointCID");
           // Now check the problematic field with the CORRECT name
           expect(blockDetails.modelStateCID).to.equal(modelCID); // Use modelStateCID
           // Add check for steps if needed: expect(blockDetails.steps).to.equal(steps);

           // Now check the helper view function
           expect(await registry.getCurrentReferenceModel()).to.equal(modelCID);

           // Check the reverse lookup mapping (uses DPoDL checkpoint CID, not model CID)
           expect(await registry.getBlockHeightForCID("QmDpodlCheckpointCID")).to.equal(1);
       });

       it("Should reward the proposer with tokens upon successful submission", async function() {
           const modelCID = "testRewardCID"; // Simpler CID string
           const t1Hash = "0x" + "0".repeat(63) + "2";
           const accuracyBPS = 9100n; // 91.00% > initial 85.00%
           const genesisReferenceCID = ""; // Changed from ethers.ZeroHash
           const steps = 1000n; // Placeholder steps value

           const initialBalance = await token.balanceOf(proposer1.address);
           const rewardAmount = await registry.blockRewardAmount();

           await registry.connect(proposer1).submitBlock(
               modelCID,                // _newModelStateCID
               "QmDpodlCheckpointCID",  // _newDpodlCheckpointCID
               accuracyBPS,             // _accuracyBPS
               steps,                   // _steps
               t1Hash,                  // _postHash
               "QmGenesisDpodlCheckpointCID" // _referenceDpodlCheckpointCID
           );

           const finalBalance = await token.balanceOf(proposer1.address);

           expect(finalBalance).to.equal(initialBalance + rewardAmount);
       });

       it("Should split reward between proposer and reference proposer", async function() {
            const firstCID = "firstRewardSplitCID";
            const secondCID = "secondRewardSplitCID";
            const t1Hash1 = "0x" + "0".repeat(63) + "A";
            const t1Hash2 = "0x" + "0".repeat(63) + "B";
            const firstAccuracyBPS = 9000n;  // First block accuracy
            const secondAccuracyBPS = 9200n; // Second block has improved accuracy
            const firstSteps = 500n;          // First block steps
            const secondSteps = 600n;         // Second block has more training steps
            const genesisRef = "";

            // ReferenceProposer submits the first block
            await registry.connect(referenceProposer).submitBlock(firstCID, "QmDpodlCheckpointCID1", firstAccuracyBPS, firstSteps, t1Hash1, "QmGenesisDpodlCheckpointCID");
            const refProposerInitialBalance = await token.balanceOf(referenceProposer.address);

            // Proposer1 submits the second block, referencing the first (with improved accuracy)
            const proposer1InitialBalance = await token.balanceOf(proposer1.address);
            await registry.connect(proposer1).submitBlock(secondCID, "QmDpodlCheckpointCID2", secondAccuracyBPS, secondSteps, t1Hash2, "QmDpodlCheckpointCID1");

            // Calculate expected rewards
            const totalReward = await registry.blockRewardAmount();
            const refShare = await registry.referenceRewardShareBPS();
            const expectedRefReward = (totalReward * refShare) / 10000n;
            const expectedProposerReward = totalReward - expectedRefReward;

            // Check balances
            const proposer1FinalBalance = await token.balanceOf(proposer1.address);
            const refProposerFinalBalance = await token.balanceOf(referenceProposer.address);

            expect(proposer1FinalBalance).to.equal(proposer1InitialBalance + expectedProposerReward);
            // Reference proposer got reward for block 1 + reference reward for block 2
            expect(refProposerFinalBalance).to.equal(refProposerInitialBalance + expectedRefReward);
        });

       it("Should give full reward to proposer if they are also the reference proposer", async function() {
            const firstCID = "selfReferenceCID1";
            const secondCID = "selfReferenceCID2";
            const t1Hash1 = "0x" + "0".repeat(63) + "C";
            const t1Hash2 = "0x" + "0".repeat(63) + "D";
            const firstAccuracyBPS = 9000n;  // First block accuracy  
            const secondAccuracyBPS = 9250n; // Second block has improved accuracy
            const firstSteps = 500n;          // First block steps
            const secondSteps = 600n;         // Second block has more training steps
            const genesisRef = "";

            // Proposer1 submits the first block
            await registry.connect(proposer1).submitBlock(firstCID, "QmDpodlCheckpointCID1", firstAccuracyBPS, firstSteps, t1Hash1, "QmGenesisDpodlCheckpointCID");
            const proposer1BalanceAfterFirst = await token.balanceOf(proposer1.address);

            // Proposer1 submits the second block, referencing their own first block (with improved accuracy)
            await registry.connect(proposer1).submitBlock(secondCID, "QmDpodlCheckpointCID2", secondAccuracyBPS, secondSteps, t1Hash2, "QmDpodlCheckpointCID1");

            // Calculate expected reward (should be full amount)
            const totalReward = await registry.blockRewardAmount();

            // Check balance
            const proposer1FinalBalance = await token.balanceOf(proposer1.address);
            expect(proposer1FinalBalance).to.equal(proposer1BalanceAfterFirst + totalReward);
       });

       it("Should fail if reference model CID doesn't match current head", async function() {
           const { registry, proposer1, proposer2 } = await loadFixture(deployContractsAndTokenFixture);
           const firstCID = "testCID";
           const secondCID = "testCID2";
           const initialAccuracy = 9000n;
           const initialSteps = 1000n;
           const initialPostHash = "0x" + "0".repeat(63) + "1";
           const genesisRef = "";
           const wrongRef = "wrongCID";

           // Submit the first block
           await registry.connect(proposer1).submitBlock(firstCID, "QmDpodlCheckpointCID1", initialAccuracy, initialSteps, initialPostHash, "QmGenesisDpodlCheckpointCID");

           // Attempt to submit the second block with the wrong reference
           await expect(registry.connect(proposer2).submitBlock(
               secondCID, "QmDpodlCheckpointCID2", initialAccuracy, initialSteps, initialPostHash, wrongRef // Using wrongRef
           )).to.be.revertedWithCustomError(registry, "InvalidReferenceModel")
             .withArgs(wrongRef, "QmDpodlCheckpointCID1"); // Expect revert with submitted and expected CIDs
       });

       it("Should allow submitting a second block referencing the first", async function() {
           const { registry, proposer1, proposer2 } = await loadFixture(deployContractsAndTokenFixture);
           const firstCID = "testCID";
           const secondCID = "testCID2";
           const firstAccuracy = 9000n;   // First block accuracy
           const secondAccuracy = 9200n;  // Second block improved accuracy
           const firstSteps = 1000n;      // First block steps
           const secondSteps = 1100n;     // Second block more steps
           const initialPostHash = "0x" + "0".repeat(63) + "1";
           const secondPostHash = "0x" + "0".repeat(63) + "2";
           const genesisRef = "";

           // Submit the first block
           await registry.connect(proposer1).submitBlock(firstCID, "QmDpodlCheckpointCID1", firstAccuracy, firstSteps, initialPostHash, "QmGenesisDpodlCheckpointCID");

           // Submit the second block referencing the first (with improved accuracy and steps)
           await expect(registry.connect(proposer2).submitBlock(
               secondCID, "QmDpodlCheckpointCID2", secondAccuracy, secondSteps, secondPostHash, "QmDpodlCheckpointCID1" // Correct reference
           )).to.emit(registry, "ModelAccepted")
             .withArgs(2, secondCID, "QmDpodlCheckpointCID2", secondAccuracy, secondPostHash, "QmDpodlCheckpointCID1", proposer2.address, anyValue);

           // Verify details of the second block
           expect(await registry.currentBlockHeight()).to.equal(2);
           expect(await registry.getCurrentReferenceModel()).to.equal(secondCID);
           const blockDetails = await registry.getBlockDetails(2);
           expect(blockDetails.modelStateCID).to.equal(secondCID); // Use modelStateCID
           expect(blockDetails.referenceModelCID).to.equal("QmDpodlCheckpointCID1"); // Reference the DPoDL checkpoint CID
       });

       it("Should fail if accuracy is below threshold", async function() {
           const { registry, proposer1, initialAccuracyThresholdBPS } = await loadFixture(deployContractsAndTokenFixture);
           const modelCID = "testAccFailCID";
           const steps = 1000n;
           const postHash = "0x" + "0".repeat(63) + "1"; // Valid post-hash
           const genesisRef = "";
           const lowAccuracy = initialAccuracyThresholdBPS - 1n; // Just below threshold

           await expect(registry.connect(proposer1).submitBlock(
               modelCID,
               "QmDpodlCheckpointCID",
               lowAccuracy, // Below threshold
               steps,
               postHash,
               "QmGenesisDpodlCheckpointCID"
           )).to.be.revertedWithCustomError(registry, "AccuracyThresholdNotMet")
             .withArgs(lowAccuracy, initialAccuracyThresholdBPS);
       });

       it("Should fail if T1 hash is not below threshold", async function() {
           const { registry, proposer1, initialAccuracyThresholdBPS, initialT1Threshold } = await loadFixture(deployContractsAndTokenFixture);
           const modelCID = "testHashFailCID";
           const steps = 1000n;
           const highAccuracy = initialAccuracyThresholdBPS; // Meets accuracy threshold
           const genesisRef = "";
           // Use a hash exactly equal to the threshold (should fail)
           const highPostHash = initialT1Threshold;

           await expect(registry.connect(proposer1).submitBlock(
               modelCID,
               "QmDpodlCheckpointCID",
               highAccuracy,
               steps,
               highPostHash, // Equal to threshold
               "QmGenesisDpodlCheckpointCID"
           )).to.be.revertedWithCustomError(registry, "HashThresholdNotMet")
             .withArgs(highPostHash, initialT1Threshold);

           // Also test with a hash greater than the threshold
            const higherPostHash = initialT1Threshold + 1n; // Should also fail
            await expect(registry.connect(proposer1).submitBlock(
                modelCID,
                "QmDpodlCheckpointCID",
                highAccuracy,
                steps,
                higherPostHash, // Greater than threshold
                "QmGenesisDpodlCheckpointCID"
            )).to.be.revertedWithCustomError(registry, "HashThresholdNotMet")
              .withArgs(higherPostHash, initialT1Threshold);
       });

       // etc.
    });

    describe("Parameter Updates", function () {
        // Tests for setT1Threshold, setTAccuracyThresholdBPS, setBlockRewardAmount, setDpdlToken
        // Including owner checks and event emissions
        it("Should allow owner to update T1 threshold", async function() {
            const { registry, owner } = await loadFixture(deployContractsAndTokenFixture);
            const newThreshold = 12345n;
            await expect(registry.connect(owner).setT1Threshold(newThreshold))
                .to.emit(registry, "ParameterUpdated")
                .withArgs("t1Threshold", newThreshold);
            expect(await registry.t1Threshold()).to.equal(newThreshold);
        });

         it("Should prevent non-owner from updating T1 threshold", async function() {
            const { registry, proposer1 } = await loadFixture(deployContractsAndTokenFixture);
            const newThreshold = 12345n;
            await expect(registry.connect(proposer1).setT1Threshold(newThreshold))
                // Standard Ownable error
                .to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount")
                .withArgs(proposer1.address);
        });

        it("Should allow owner to update Accuracy threshold BPS", async function() {
            const { registry, owner } = await loadFixture(deployContractsAndTokenFixture);
            const newThresholdBPS = 9000n; // 90.00%
            await expect(registry.connect(owner).setTAccuracyThresholdBPS(newThresholdBPS))
                .to.emit(registry, "ParameterUpdated")
                .withArgs("tAccuracyThresholdBPS", newThresholdBPS);
            expect(await registry.tAccuracyThresholdBPS()).to.equal(newThresholdBPS);
        });

        it("Should prevent non-owner from updating Accuracy threshold BPS", async function() {
            const { registry, proposer1 } = await loadFixture(deployContractsAndTokenFixture);
            const newThresholdBPS = 9000n;
            await expect(registry.connect(proposer1).setTAccuracyThresholdBPS(newThresholdBPS))
                .to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount")
                .withArgs(proposer1.address);
        });

        it("Should fail updating Accuracy BPS if value > 10000", async function() {
            const { registry, owner } = await loadFixture(deployContractsAndTokenFixture);
            const invalidThresholdBPS = 10001n;
            await expect(registry.connect(owner).setTAccuracyThresholdBPS(invalidThresholdBPS))
                .to.be.revertedWith("Accuracy BPS cannot exceed 10000");
        });

        it("Should allow owner to update block reward amount", async function() {
            const { registry, owner } = await loadFixture(deployContractsAndTokenFixture);
            const newReward = toWei(50); // 50 DPDL
            await expect(registry.connect(owner).setBlockRewardAmount(newReward))
                .to.emit(registry, "ParameterUpdated")
                .withArgs("blockRewardAmount", newReward);
            expect(await registry.blockRewardAmount()).to.equal(newReward);
        });

        it("Should prevent non-owner from updating block reward amount", async function() {
            const { registry, proposer1 } = await loadFixture(deployContractsAndTokenFixture);
            const newReward = toWei(50);
            await expect(registry.connect(proposer1).setBlockRewardAmount(newReward))
                .to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount")
                .withArgs(proposer1.address);
        });

        it("Should allow owner to update token address", async function() {
            const { registry, owner, addrs } = await loadFixture(deployContractsAndTokenFixture);
            const newTokenAddress = addrs[0].address; // Use some other address
            await expect(registry.connect(owner).setDpdlToken(newTokenAddress))
                .to.emit(registry, "ParameterUpdated")
                .withArgs("dpdlToken", BigInt(newTokenAddress)); // Event emits address as uint
            expect(await registry.dpdlToken()).to.equal(newTokenAddress);
        });

        it("Should prevent non-owner from updating token address", async function() {
            const { registry, proposer1, addrs } = await loadFixture(deployContractsAndTokenFixture);
            const newTokenAddress = addrs[0].address;
            await expect(registry.connect(proposer1).setDpdlToken(newTokenAddress))
                .to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount")
                .withArgs(proposer1.address);
        });

        it("Should fail updating token address to the zero address", async function() {
            const { registry, owner } = await loadFixture(deployContractsAndTokenFixture);
            await expect(registry.connect(owner).setDpdlToken(ethers.ZeroAddress))
                .to.be.revertedWithCustomError(registry, "ZeroAddress");
        });

        // TODO: Tests for setDpdlToken
        // etc.
    });

     describe("View Functions", function () {
        // Tests for getCurrentReferenceModel, getBlockDetails, getBlockHeightForCID
         it("Should return correct reference model CID (genesis and after first block)", async function() {
            const { registry, owner, proposer1 } = await loadFixture(deployContractsAndTokenFixture);
            const firstCID = "testViewCID";
            const initialAccuracy = 9000n;
            const initialSteps = 1000n;
            const initialPostHash = "0x" + "0".repeat(63) + "1";
            const genesisRef = "";

            // Check initial state (should be genesis model state CID)
            expect(await registry.getCurrentReferenceModel()).to.equal("QmGenesisModelStateCID");

            // Submit the first block
            await registry.connect(proposer1).submitBlock(firstCID, "QmDpodlCheckpointCID1", initialAccuracy, initialSteps, initialPostHash, "QmGenesisDpodlCheckpointCID");

            // Check after first block (should be the first block's CID)
            expect(await registry.getCurrentReferenceModel()).to.equal(firstCID);
        });

         it("Should return correct block details for a valid block", async function() {
            const { registry, owner, proposer1 } = await loadFixture(deployContractsAndTokenFixture);
            const modelCID = "testDetailsCID";
            const accuracyBPS = 9100n;
            const steps = 1500n;
            const postHash = "0x" + "0".repeat(63) + "3";
            const genesisRef = "";

            // Submit the first block
            await registry.connect(proposer1).submitBlock(modelCID, "QmDpodlCheckpointDetails", accuracyBPS, steps, postHash, "QmGenesisDpodlCheckpointCID");

            // Get details of block 1
            const blockDetails = await registry.getBlockDetails(1);

            // Verify all fields
            expect(blockDetails.blockHeight).to.equal(1);
            expect(blockDetails.modelStateCID).to.equal(modelCID);
            expect(blockDetails.accuracyBPS).to.equal(accuracyBPS);
            expect(blockDetails.steps).to.equal(steps);
            expect(blockDetails.postHash).to.equal(postHash);
            expect(blockDetails.referenceModelCID).to.equal("QmGenesisDpodlCheckpointCID");
            expect(blockDetails.proposer).to.equal(proposer1.address);
            // Timestamp is harder to check exactly, check it's non-zero
            expect(blockDetails.timestamp).to.be.gt(0);
        });

        it("Should return zeroed struct for block 0 or non-existent block height", async function() {
            const { registry } = await loadFixture(deployContractsAndTokenFixture);

            // Block 0 should not exist / be zeroed
            const block0Details = await registry.getBlockDetails(0);
            expect(block0Details.proposer).to.equal(ethers.ZeroAddress);
            expect(block0Details.blockHeight).to.equal(0);
            expect(block0Details.modelStateCID).to.equal(""); // Expect empty string for string fields

             // A block height far in the future
             const futureBlockDetails = await registry.getBlockDetails(9999);
             expect(futureBlockDetails.proposer).to.equal(ethers.ZeroAddress);
             expect(futureBlockDetails.blockHeight).to.equal(0);
        });

         it("Should return correct block height for a known CID", async function() {
            const { registry, owner, proposer1 } = await loadFixture(deployContractsAndTokenFixture);
            const modelCID = "testHeightLookupCID";
            const accuracyBPS = 9100n;
            const steps = 1500n;
            const postHash = "0x" + "0".repeat(63) + "3";
            const genesisRef = "";

            // Submit the first block
            await registry.connect(proposer1).submitBlock(modelCID, "QmDpodlCheckpointHeight", accuracyBPS, steps, postHash, "QmGenesisDpodlCheckpointCID");

            // Check the lookup (uses DPoDL checkpoint CID, not model CID)
            expect(await registry.getBlockHeightForCID("QmDpodlCheckpointHeight")).to.equal(1);
        });

        it("Should return 0 for an unknown CID", async function() {
            const { registry } = await loadFixture(deployContractsAndTokenFixture);
            const unknownCID = "nonExistentCID";

            expect(await registry.getBlockHeightForCID(unknownCID)).to.equal(0);
        });
         // etc.
     });

}); 