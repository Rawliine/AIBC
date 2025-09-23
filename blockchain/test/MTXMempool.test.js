// blockchain/test/MTXMempool.test.js
const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs"); // For timestamp checking

describe("MTXMempool", function () {
    // Define the fixture for deploying the MTXMempool contract
    async function deployMempoolFixture() {
        // Get signers
        const [owner, submitter1, submitter2, ...addrs] = await ethers.getSigners();

        // Deploy the MTXMempool contract
        const MTXMempool = await ethers.getContractFactory("MTXMempool");
        const mempool = await MTXMempool.deploy(owner.address); // Deploy with initial owner
        await mempool.waitForDeployment();

        // Return all necessary objects
        return { mempool, owner, submitter1, submitter2, addrs };
    }

    // --- Test Suites ---

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            const { mempool, owner } = await loadFixture(deployMempoolFixture);
            expect(await mempool.owner()).to.equal(owner.address);
        });

        it("Should initialize nextMtxId to 1", async function () {
            const { mempool } = await loadFixture(deployMempoolFixture);
            expect(await mempool.nextMtxId()).to.equal(1);
        });

        it("Should initialize MTX count to 0", async function () {
            const { mempool } = await loadFixture(deployMempoolFixture);
            expect(await mempool.getMtxCount()).to.equal(0);
        });
    });

    describe("MTX Submission", function () {
        it("Should allow a user to submit a valid MTX", async function() {
            const { mempool, submitter1 } = await loadFixture(deployMempoolFixture);
            const ipfsCID = "QmTestMTXCid";
            const accuracyBPS = 8000n; // 80.00%
            const steps = 500n;
            const referenceModelCID = "QmBaseModelCID";

            // Check event emission
            await expect(mempool.connect(submitter1).submitMtx(
                ipfsCID,
                accuracyBPS,
                steps,
                referenceModelCID
            ))
                .to.emit(mempool, "MtxSubmitted")
                .withArgs(
                    1,                 // Expected mtxId
                    ipfsCID,
                    accuracyBPS,
                    referenceModelCID,
                    submitter1.address,
                    anyValue,          // timestamp
                    0                  // status (Pending = 0)
                );

            // Check state using getMtxDetails
            const details = await mempool.getMtxDetails(1);
            expect(details.mtxId).to.equal(1);
            expect(details.ipfsCID).to.equal(ipfsCID);
            expect(details.accuracyBPS).to.equal(accuracyBPS);
            expect(details.steps).to.equal(steps);
            expect(details.referenceModelCID).to.equal(referenceModelCID);
            expect(details.submitter).to.equal(submitter1.address);
            expect(details.isValid).to.equal(true);
            expect(details.timestamp).to.be.gt(0);
        });

        it("Should increment MTX ID and count on multiple submissions", async function() {
            const { mempool, submitter1, submitter2 } = await loadFixture(deployMempoolFixture);

            // Initial state
            expect(await mempool.nextMtxId()).to.equal(1);
            expect(await mempool.getMtxCount()).to.equal(0);

            // Submit first MTX
            await mempool.connect(submitter1).submitMtx("CID1", 8000n, 100n, "ref0");
            expect(await mempool.nextMtxId()).to.equal(2);
            expect(await mempool.getMtxCount()).to.equal(1);
            const details1 = await mempool.getMtxDetails(1);
            expect(details1.ipfsCID).to.equal("CID1");

            // Submit second MTX
            await mempool.connect(submitter2).submitMtx("CID2", 8100n, 120n, "ref1");
            expect(await mempool.nextMtxId()).to.equal(3);
            expect(await mempool.getMtxCount()).to.equal(2);
            const details2 = await mempool.getMtxDetails(2);
            expect(details2.ipfsCID).to.equal("CID2");
            expect(details2.submitter).to.equal(submitter2.address);
        });
    });

    describe("View Functions", function () {
        it("getMtxDetails should revert for an invalid MTX ID", async function() {
            const { mempool } = await loadFixture(deployMempoolFixture);

            // Try getting details for ID 0 (never valid)
            await expect(mempool.getMtxDetails(0))
                .to.be.revertedWithCustomError(mempool, "InvalidMtxId")
                .withArgs(0);

            // Try getting details for ID 1 (before submission)
             await expect(mempool.getMtxDetails(1))
                .to.be.revertedWithCustomError(mempool, "InvalidMtxId")
                .withArgs(1);
        });

        it("getMtxDetails should return correct details for a valid ID (covered in submission tests)", async function() {
             // This functionality is largely covered by the successful submission test
             // We can add a simple check here for completeness if desired
             const { mempool, submitter1 } = await loadFixture(deployMempoolFixture);
             const ipfsCID = "QmViewTestCID";
             await mempool.connect(submitter1).submitMtx(ipfsCID, 7500n, 300n, "refView");
             const details = await mempool.getMtxDetails(1);
             expect(details.ipfsCID).to.equal(ipfsCID);
        });

        it("getMtxCount should return the correct count (covered in submission tests)", async function() {
            // This functionality is covered by the multiple submission test
            // We can add a simple check here
            const { mempool, submitter1 } = await loadFixture(deployMempoolFixture);
            expect(await mempool.getMtxCount()).to.equal(0);
            await mempool.connect(submitter1).submitMtx("CID_Count1", 8000n, 100n, "refC0");
            expect(await mempool.getMtxCount()).to.equal(1);
            await mempool.connect(submitter1).submitMtx("CID_Count2", 8100n, 110n, "refC1");
            expect(await mempool.getMtxCount()).to.equal(2);
        });
    });

}); 