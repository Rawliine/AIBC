const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");
const { anyValue } = require("@nomicfoundation/hardhat-chai-matchers/withArgs");

describe("TaskRegistry", function () {
    // Define the fixture for deploying the TaskRegistry contract
    async function deployTaskRegistryFixture() {
        // Get signers
        const [owner, publisher1, user1, ...addrs] = await ethers.getSigners();

        // Deploy the TaskRegistry contract
        const TaskRegistry = await ethers.getContractFactory("TaskRegistry");
        const registry = await TaskRegistry.deploy(owner.address); // Deploy with initial owner
        await registry.waitForDeployment();

        // Return all necessary objects
        return { registry, owner, publisher1, user1, addrs };
    }

    // --- Test Suites ---

    describe("Deployment", function () {
        it("Should set the right owner", async function () {
            const { registry, owner } = await loadFixture(deployTaskRegistryFixture);
            expect(await registry.owner()).to.equal(owner.address);
        });

        it("Should initialize task count to 0", async function () {
            const { registry } = await loadFixture(deployTaskRegistryFixture);
            expect(await registry.getTaskCount()).to.equal(0);
        });
    });

    describe("Task Submission", function () {
        it("Should allow a user to submit a task", async function() {
            const { registry, publisher1 } = await loadFixture(deployTaskRegistryFixture);
            const datasetId = "QmDatasetCID";
            const criteria = "Accuracy > 90%";
            const targetAccBPS = 9000n;
            const reward = ethers.parseEther("10"); // Example reward
            const duration = 86400n; // 1 day in seconds

            await expect(registry.connect(publisher1).submitTask(
                datasetId,
                criteria,
                targetAccBPS,
                reward,
                duration
            ))
                .to.emit(registry, "TaskSubmitted")
                .withArgs(1, publisher1.address, datasetId, targetAccBPS, reward, duration);

            // Check state
            expect(await registry.getTaskCount()).to.equal(1);
            const taskDetails = await registry.getTaskDetails(1);
            expect(taskDetails.taskId).to.equal(1);
            expect(taskDetails.publisher).to.equal(publisher1.address);
            expect(taskDetails.datasetIdentifier).to.equal(datasetId);
            expect(taskDetails.targetAccuracyBPS).to.equal(targetAccBPS);
            expect(taskDetails.rewardPool).to.equal(reward);
            expect(taskDetails.status).to.equal(0); // TaskStatus.Pending
            expect(taskDetails.startTimestamp).to.equal(0);

            const publisherTasks = await registry.getPublisherTasks(publisher1.address);
            expect(publisherTasks).to.have.lengthOf(1);
            expect(publisherTasks[0]).to.equal(1);
        });

         it("Should increment task ID on multiple submissions", async function() {
            const { registry, publisher1, user1 } = await loadFixture(deployTaskRegistryFixture);
            await registry.connect(publisher1).submitTask("ds1", "c1", 8000n, 10n, 86400n); // 8k -> 8000n, 10 -> 10n (assuming reward), 1d -> 86400n
            await registry.connect(user1).submitTask("ds2", "c2", 9000n, 20n, 172800n); // 9k -> 9000n, 20 -> 20n (assuming reward), 2d -> 172800n

            expect(await registry.getTaskCount()).to.equal(2);
            const task2Details = await registry.getTaskDetails(2);
            expect(task2Details.publisher).to.equal(user1.address);
            expect(task2Details.datasetIdentifier).to.equal("ds2");

            const user1Tasks = await registry.getPublisherTasks(user1.address);
            expect(user1Tasks).to.have.lengthOf(1);
            expect(user1Tasks[0]).to.equal(2);
        });
    });

    describe("Task Status Updates", function () {
        let registry, owner, publisher1, taskId;
        const datasetId = "QmStatusDataset";
        const criteria = "Status Test";
        const targetAccBPS = 9500n;
        const reward = ethers.parseEther("5");
        const duration = 3600n; // 1 hour

        // Setup: Submit a task before each status test
        beforeEach(async function(){
            ({ registry, owner, publisher1 } = await loadFixture(deployTaskRegistryFixture));
            // Submit task as publisher1
            const tx = await registry.connect(publisher1).submitTask(datasetId, criteria, targetAccBPS, reward, duration);
            const receipt = await tx.wait();
            // A simple way to get the emitted taskId from the event
            const filter = registry.filters.TaskSubmitted();
            const events = await registry.queryFilter(filter, receipt.blockNumber);
            taskId = events[0].args.taskId;
        })

        it("Should allow owner to start a pending task", async function() {
            await expect(registry.connect(owner).startTask(taskId))
                .to.emit(registry, "TaskStatusUpdated")
                .withArgs(taskId, 1 /* Active */, anyValue);

            const taskDetails = await registry.getTaskDetails(taskId);
            expect(taskDetails.status).to.equal(1); // TaskStatus.Active
            expect(taskDetails.startTimestamp).to.be.gt(0);
        });

        it("Should prevent non-owner from starting a task", async function() {
            await expect(registry.connect(publisher1).startTask(taskId))
                .to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount");
        });

        it("Should prevent starting a non-pending task", async function() {
            await registry.connect(owner).startTask(taskId); // Start it first
            await expect(registry.connect(owner).startTask(taskId))
                .to.be.revertedWithCustomError(registry, "InvalidTaskStatusTransition");
        });

        it("Should allow owner to complete an active task", async function() {
            await registry.connect(owner).startTask(taskId); // Must be active first
            await expect(registry.connect(owner).completeTask(taskId))
                 .to.emit(registry, "TaskStatusUpdated")
                 .withArgs(taskId, 2 /* Completed */, anyValue);

            const taskDetails = await registry.getTaskDetails(taskId);
            expect(taskDetails.status).to.equal(2); // TaskStatus.Completed
            expect(taskDetails.endTimestamp).to.be.gt(0);
        });

        it("Should allow publisher to complete an active task", async function() {
             await registry.connect(owner).startTask(taskId);
             await expect(registry.connect(publisher1).completeTask(taskId))
                 .to.emit(registry, "TaskStatusUpdated")
                 .withArgs(taskId, 2 /* Completed */, anyValue);
            const taskDetails = await registry.getTaskDetails(taskId);
            expect(taskDetails.status).to.equal(2); 
        });

        it("Should prevent completing a non-active task", async function() {
            // Test completing pending task
            await expect(registry.connect(owner).completeTask(taskId))
                .to.be.revertedWithCustomError(registry, "InvalidTaskStatusTransition");
            // Test completing already completed task
            await registry.connect(owner).startTask(taskId);
            await registry.connect(owner).completeTask(taskId);
             await expect(registry.connect(owner).completeTask(taskId))
                .to.be.revertedWithCustomError(registry, "InvalidTaskStatusTransition");
        });
        
         it("Should prevent non-owner/non-publisher from completing", async function(){
             const { user1 } = await loadFixture(deployTaskRegistryFixture);
             await registry.connect(owner).startTask(taskId);
             await expect(registry.connect(user1).completeTask(taskId))
                 .to.be.revertedWithCustomError(registry, "Unauthorized");
         });

        it("Should allow owner to cancel a pending task", async function() {
            await expect(registry.connect(owner).cancelTask(taskId))
                 .to.emit(registry, "TaskStatusUpdated")
                 .withArgs(taskId, 3 /* Cancelled */, anyValue);
            const taskDetails = await registry.getTaskDetails(taskId);
            expect(taskDetails.status).to.equal(3);
            expect(taskDetails.endTimestamp).to.be.gt(0);
        });
        
        it("Should allow owner to cancel an active task", async function() {
            await registry.connect(owner).startTask(taskId);
            await expect(registry.connect(owner).cancelTask(taskId))
                 .to.emit(registry, "TaskStatusUpdated")
                 .withArgs(taskId, 3 /* Cancelled */, anyValue);
            const taskDetails = await registry.getTaskDetails(taskId);
            expect(taskDetails.status).to.equal(3);
        });

        it("Should allow publisher to cancel a pending task", async function() {
             await expect(registry.connect(publisher1).cancelTask(taskId))
                 .to.emit(registry, "TaskStatusUpdated")
                 .withArgs(taskId, 3 /* Cancelled */, anyValue);
            const taskDetails = await registry.getTaskDetails(taskId);
            expect(taskDetails.status).to.equal(3);
        });

        it("Should prevent cancelling a completed task", async function() {
            await registry.connect(owner).startTask(taskId);
            await registry.connect(owner).completeTask(taskId);
            await expect(registry.connect(owner).cancelTask(taskId))
                .to.be.revertedWithCustomError(registry, "InvalidTaskStatusTransition");
        });

         it("Should prevent non-owner/non-publisher from cancelling", async function(){
             const { user1 } = await loadFixture(deployTaskRegistryFixture);
             await expect(registry.connect(user1).cancelTask(taskId))
                 .to.be.revertedWithCustomError(registry, "Unauthorized");
         });
    });

    // TODO: Add tests for associateModelToTask (might require mocking or another contract)
     describe("Model Association", function () {
         it("Should allow associating a model CID with a task", async function(){
             const { registry, owner, publisher1 } = await loadFixture(deployTaskRegistryFixture);
             const tx = await registry.connect(publisher1).submitTask("ds_assoc", "c_assoc", 9000n, 10n, 86400n); // 9k -> 9000n, 10 -> 10n, 1d -> 86400n
             const receipt = await tx.wait();
             const filter = registry.filters.TaskSubmitted();
             const events = await registry.queryFilter(filter, receipt.blockNumber);
             const taskId = events[0].args.taskId;
             const modelCID = "QmModelAssociatedCID";

             // NOTE: associateModelToTask is external, needs access control in real scenario
             // For now, assume anyone can call it for testing structure
             await expect(registry.associateModelToTask(taskId, modelCID))
                 .to.emit(registry, "ModelAssociatedToTask")
                 .withArgs(taskId, modelCID);

             const taskDetails = await registry.getTaskDetails(taskId);
             expect(taskDetails.associatedModelCIDs).to.have.lengthOf(1);
             expect(taskDetails.associatedModelCIDs[0]).to.equal(modelCID);
         });

          it("Should revert associating model if taskId is invalid", async function(){
             const { registry } = await loadFixture(deployTaskRegistryFixture);
             await expect(registry.associateModelToTask(999, "badCID"))
                 .to.be.revertedWithCustomError(registry, "InvalidTaskId");
         });
     });
}); 