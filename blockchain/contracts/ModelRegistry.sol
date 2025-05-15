// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol"; // Interface for interacting with the token
import "./DPoDLToken.sol"; // Import the specific token contract type
import "./MTXMempool.sol"; // ADDED: Import the MTXMempool contract to access its types

// Interface for MTXMempool
interface IMTXMempool {
    // Status enum and ModelTransaction struct are now defined in MTXMempool.sol
    // and will be accessed via MTXMempool.Status and MTXMempool.ModelTransaction

    function updateMtxStatus(uint256 mtxId, MTXMempool.Status newStatus) external; // Use MTXMempool.Status
    
    function getMtxDetails(uint256 mtxId) external view returns (MTXMempool.ModelTransaction memory);
}

/**
 * @title ModelRegistry
 * @dev Stores the canonical chain of validated D-PoDL models (blocks).
 *      Enforces consensus rules (T1 hash threshold, T_acc accuracy threshold).
 *      Manages D-PoDL parameters and rewards proposers.
 */
contract ModelRegistry is Ownable {

    // --- Structs ---

    /**
     * @dev Represents a single validated block in the D-PoDL model chain.
     */
    struct ModelBlock {
        uint256 blockHeight;          // Sequential ID of the block
        string modelStateCID;         // IPFS CID of the model's actual state_dict
        string dpodlCheckpointCID;    // IPFS CID of the D-PoDL state/proofs/metadata file for this block
        uint256 accuracyBPS;          // Accuracy in Basis Points (e.g., 9500 for 95.00%)
        uint256 steps;                // Training steps performed for this model
        uint256 postHash;             // The hash value that met the T1 threshold
        string referenceModelCID;     // CID of the model this block was based on (previous block's CID)
        address proposer;             // Address that successfully submitted this block
        uint256 timestamp;            // Timestamp when the block was accepted
    }

    // --- State Variables ---

    // D-PoDL Parameters (public for easy reading, modifiable by owner)
    uint256 public t1Threshold;         // Target hash threshold (lower is harder)
    uint256 public tAccuracyThresholdBPS; // Target accuracy threshold in Basis Points
    uint256 public blockRewardAmount;   // Amount of DPDL tokens rewarded per block for new blocks
    uint256 public mtxRewardAmount;     // Amount of DPDL tokens rewarded for a processed MTX
    uint256 public minTrainingSteps;    // Minimum training steps required
    uint256 public maxTrainingSteps;    // Maximum training steps allowed to prevent overtraining
    uint256 public referenceRewardShareBPS; // Share of reward for reference model proposer (0-10000)

    // Additional state variables for model improvement verification
    uint256 public minAccuracyImprovementBPS; // Minimum accuracy improvement in BPS
    uint256 public minStepImprovement;         // Minimum additional steps required

    // Token Contract
    IERC20 public dpdlToken;             // Address of the DPoDLToken contract

    // MTXMempool Contract Interface
    IMTXMempool public mtxMempoolContract;

    // Model Chain Storage
    mapping(uint256 => ModelBlock) public modelBlocks; // blockHeight => ModelBlock data
    uint256 public currentBlockHeight;                 // Height of the latest accepted block
    mapping(string => uint256) public dpodlCheckpointCIDToBlockHeight; // NEW: dpodlCheckpointCID => blockHeight

    // Current Global Reference Model CIDs (updated by new blocks or selected MTXs)
    string public currentModelStateCID;          // CID of the model state (weights) to train from
    string public currentDpodlCheckpointCID;    // CID of the D-PoDL checkpoint data for the currentModelStateCID

    // Additional state for tracking MTX processing
    uint256 public lastGlobalModelUpdateTime; // ADDED: Timestamp of the last global model update via MTX
    uint256 public lastProcessedMtxId;      // ADDED: ID of the last MTX processed

    // Genesis Block Info (optional, can be set in constructor or first submission)
    // string public genesisCID = ""; // REMOVED: Placeholder for potential genesis model. Replaced by currentModelStateCID initialization.

    // --- Events ---

    /**
     * @dev Emitted when a new model block is successfully validated and added to the registry.
     */
    event ModelAccepted(
        uint256 indexed blockHeight,
        string modelStateCID,         // NEW
        string dpodlCheckpointCID,    // NEW
        uint256 accuracyBPS,
        uint256 postHash,
        string referenceModelCID,
        address indexed proposer,
        uint256 timestamp
    );

    /**
     * @dev Emitted when a D-PoDL parameter is updated by the owner.
     */
    event ParameterUpdated(string parameterName, uint256 newValue);

    /**
     * @dev Emitted when a reward minting operation fails.
     */
    event RewardMintFailed(address indexed to, uint256 amount); // For block submission rewards

    /**
     * @dev Emitted when the global reference model (state and DPoDL checkpoint) is updated,
     *      either by a new block or by processing an MTX.
     */
    event GlobalReferenceModelUpdated(
        string modelStateCID,
        string dpodlCheckpointCID,
        address indexed updater,
        uint256 indexed id, // mtxId if from MTX (isBlockUpdate=false), blockHeight if from Block (isBlockUpdate=true)
        bool isBlockUpdate // True if update was from a new block, false if from an MTX
    );

    /**
     * @dev Emitted when a reward is distributed for processing an MTX.
     */
    event RewardDistributedForMtx(uint256 indexed mtxId, address indexed submitter, uint256 rewardAmount);

    // New Debug Event
    event DebugStep(uint256 indexed step);

    event UpdateReferenceModelFromMtxCalled(uint256 mtxId, string modelCID, string dpodlCID, address caller);

    // --- Errors ---
    error InvalidReferenceModel(string submittedCID, string expectedCID);
    error HashThresholdNotMet(uint256 submittedHash, uint256 threshold);
    error AccuracyThresholdNotMet(uint256 submittedAccuracyBPS, uint256 thresholdBPS);
    error StepsOutOfRange(uint256 submittedSteps, uint256 minSteps, uint256 maxSteps);
    error InvalidTokenAddress();
    error ZeroAddress();
    error ZeroValue();
    error InsufficientImprovement(uint256 accuracyBPS, uint256 referenceAccuracyBPS, uint256 minImprovementBPS);
    error InsufficientTrainingSteps(uint256 steps, uint256 referenceSteps, uint256 minStepImprovement);

    // --- Constructor ---

    /**
     * @dev Initializes the contract, setting D-PoDL parameters and the token address.
     * @param _initialT1Threshold The initial T1 hash difficulty threshold.
     * @param _initialTAccuracyThresholdBPS The initial accuracy threshold in Basis Points (1-10000).
     * @param _initialBlockRewardAmount The initial DPDL token reward per accepted block.
     * @param _initialMinTrainingSteps The minimum number of training steps required for model submission.
     * @param _initialMaxTrainingSteps The maximum number of training steps allowed (to prevent overtraining).
     * @param _initialMinAccuracyImprovementBPS The minimum accuracy improvement required over reference model.
     * @param _initialMinStepImprovement The minimum additional training steps required over reference model.
     * @param _initialReferenceRewardShareBPS The initial reference reward share in Basis Points (0-10000).
     * @param _tokenAddress The address of the deployed DPoDLToken contract.
     * @param _initialOwner The address designated as the contract owner.
     * @param _initialGenesisModelStateCID The IPFS CID of the initial (genesis) model state.
     * @param _initialGenesisDpodlCheckpointCID The IPFS CID of the DPoDL checkpoint for the genesis model (can be empty string if not applicable).
     * @param _initialMtxRewardAmount The initial DPDL token reward for a processed MTX.
     */
    constructor(
        uint256 _initialT1Threshold,
        uint256 _initialTAccuracyThresholdBPS,
        uint256 _initialBlockRewardAmount,
        uint256 _initialMinTrainingSteps,
        uint256 _initialMaxTrainingSteps,
        uint256 _initialMinAccuracyImprovementBPS,
        uint256 _initialMinStepImprovement,
        uint256 _initialReferenceRewardShareBPS,
        address _tokenAddress,
        address _initialOwner, // Pass initial owner explicitly
        string memory _initialGenesisModelStateCID,
        string memory _initialGenesisDpodlCheckpointCID,
        uint256 _initialMtxRewardAmount // New constructor argument
    ) Ownable(_initialOwner) {
        if (_tokenAddress == address(0)) revert ZeroAddress();
        if (_initialOwner == address(0)) revert ZeroAddress(); // Ensure owner is not zero address
        // Basic sanity check for accuracy threshold (e.g., between 0% and 100%)
        if (_initialTAccuracyThresholdBPS > 10000) revert("Accuracy BPS cannot exceed 10000"); 
        // Basic sanity check for training steps
        if (_initialMinTrainingSteps > _initialMaxTrainingSteps) revert("Min steps cannot exceed max steps");
        if (_initialReferenceRewardShareBPS > 10000) revert("Reference reward share BPS cannot exceed 10000");

        t1Threshold = _initialT1Threshold;
        tAccuracyThresholdBPS = _initialTAccuracyThresholdBPS;
        blockRewardAmount = _initialBlockRewardAmount;
        minTrainingSteps = _initialMinTrainingSteps;
        maxTrainingSteps = _initialMaxTrainingSteps;
        minAccuracyImprovementBPS = _initialMinAccuracyImprovementBPS;
        minStepImprovement = _initialMinStepImprovement;
        referenceRewardShareBPS = _initialReferenceRewardShareBPS;
        dpdlToken = IERC20(_tokenAddress);
        currentBlockHeight = 0; // Initialize block height

        // Initialize current global model CIDs from genesis values
        // Basic validation for genesis CIDs (must not be empty for model state)
        if (bytes(_initialGenesisModelStateCID).length == 0) revert("Genesis model state CID cannot be empty");
        currentModelStateCID = _initialGenesisModelStateCID;
        currentDpodlCheckpointCID = _initialGenesisDpodlCheckpointCID; // Can be empty if no specific DPoDL checkpoint for genesis
        mtxRewardAmount = _initialMtxRewardAmount; // Initialize MTX reward amount

        emit ParameterUpdated("t1Threshold", _initialT1Threshold);
        emit ParameterUpdated("tAccuracyThresholdBPS", _initialTAccuracyThresholdBPS);
        emit ParameterUpdated("blockRewardAmount", _initialBlockRewardAmount);
        emit ParameterUpdated("minTrainingSteps", _initialMinTrainingSteps);
        emit ParameterUpdated("maxTrainingSteps", _initialMaxTrainingSteps);
        emit ParameterUpdated("minAccuracyImprovementBPS", _initialMinAccuracyImprovementBPS);
        emit ParameterUpdated("minStepImprovement", _initialMinStepImprovement);
        emit ParameterUpdated("referenceRewardShareBPS", _initialReferenceRewardShareBPS);
        emit ParameterUpdated("dpdlToken", uint256(uint160(_tokenAddress))); // Emit address as uint
        emit ParameterUpdated("mtxRewardAmount", _initialMtxRewardAmount); // Emit new param

        // Emit the initial state of the global reference model
        emit GlobalReferenceModelUpdated(
            currentModelStateCID,
            currentDpodlCheckpointCID,
            address(this), // Updater is the contract itself during deployment
            0,             // ID is 0 for genesis/initialization (block height 0)
            true           // isBlockUpdate is true, as it establishes the first baseline
        );
    }

    // --- Core Functions ---

    /**
     * @dev Verifies that a model has made sufficient improvement over its reference model.
     * @param _accuracyBPS The accuracy of the submitted model.
     * @param _steps The training steps of the submitted model.
     * @param _referenceDpodlCheckpointCID The DPoDL Checkpoint CID of the reference model this submission was based on.
     * @return A boolean indicating if the improvement is sufficient.
     */
    function verifyModelImprovement(
        uint256 _accuracyBPS,
        uint256 _steps,
        string memory _referenceDpodlCheckpointCID
    ) public view returns (bool) {
        // If there's no reference DPoDL checkpoint CID provided, it implies a submission against the absolute genesis
        // or a state where no DPoDL checkpoint is yet established as the reference.
        if (bytes(_referenceDpodlCheckpointCID).length == 0) {
            // This case should ideally only be true if currentDpodlCheckpointCID is also empty (true genesis)
            // or if the system allows submissions without explicit reference under certain conditions.
            // For simplicity, if no reference is given, and we are at block 0, assume it's a genesis-like submission.
            if (currentBlockHeight == 0) return true;
            // Otherwise, a reference is generally expected if blocks exist.
            // Depending on policy, could revert here or return false.
            // For now, let allow if at block 0, otherwise false if empty ref passed beyond genesis. 
            return false; 
        }

        // If currentBlockHeight is 0, it means we are checking against the initial DPoDL checkpoint set by constructor.
        // The _referenceDpodlCheckpointCID must match this initial currentDpodlCheckpointCID.
        if (currentBlockHeight == 0) {
            if (keccak256(abi.encodePacked(_referenceDpodlCheckpointCID)) == keccak256(abi.encodePacked(currentDpodlCheckpointCID))) {
                return true; // Improvement check bypassed for first block against constructor-set DPoDL checkpoint
            }
            // If it doesn't match, it's an invalid reference for the very first block submission.
            revert("Invalid reference DPoDL checkpoint for initial block");
        }

        // Get reference model block height using the DPoDL checkpoint CID
        uint256 referenceBlockHeight = dpodlCheckpointCIDToBlockHeight[_referenceDpodlCheckpointCID];
        if (referenceBlockHeight == 0) {
            // This means the provided _referenceDpodlCheckpointCID is not a known block's DPoDL checkpoint.
            // This could happen if it refers to an MTX-updated currentDpodlCheckpointCID that hasn't been consolidated into a block yet,
            // OR if it's simply an invalid/unknown CID.
            // For verifyModelImprovement (called by submitBlock), the reference *must* be an existing block.
            // If an MTX updated currentDpodlCheckpointCID, a new block referencing it would need that MTX's stats.
            // This simplification assumes submitBlock always references a prior *block's* DPoDL checkpoint.
            revert("Reference DPoDL checkpoint CID not found in block history");
        }

        ModelBlock memory referenceBlock = modelBlocks[referenceBlockHeight];
        
        // Check for accuracy improvement
        if (_accuracyBPS < referenceBlock.accuracyBPS + minAccuracyImprovementBPS) {
            return false;
        }

        // Check for step improvement
        if (_steps < referenceBlock.steps + minStepImprovement) {
            return false;
        }

        return true;
    }

    /**
     * @dev Allows a proposer to submit a potential new model block.
     *      Validates the submission against D-PoDL consensus rules.
     *      If valid, adds the block to the registry and rewards the proposer.
     * @param _newModelStateCID The IPFS CID of the model's actual state_dict.
     * @param _newDpodlCheckpointCID The IPFS CID of the D-PoDL state/proofs/metadata file for this block.
     * @param _accuracyBPS The accuracy achieved by the model (in Basis Points, 1-10000).
     * @param _steps The number of training steps performed.
     * @param _postHash The Post-Hash value calculated by the worker.
     * @param _referenceDpodlCheckpointCID The DPoDL Checkpoint CID of the model this block was based on.
     */
    function submitBlock(
        string memory _newModelStateCID,       // NEW: CID of the actual model state dict
        string memory _newDpodlCheckpointCID, // NEW: CID of the D-PoDL metadata/proofs checkpoint for this block
        uint256 _accuracyBPS,
        uint256 _steps,
        uint256 _postHash,
        string memory _referenceDpodlCheckpointCID // NEW: The DPoDL Checkpoint CID of the model this block was based on
    ) public {
        // --- Validation Checks ---

        // 1. Check if based on the correct reference DPoDL checkpoint (from current global state)
        string memory expectedReferenceDpodlCheckpointCID = getCurrentReferenceDpodlCheckpointCID();
        
        // Handle case where initial model might not have a DPoDL checkpoint CID (empty string)
        // A submission against such a genesis would pass an empty _referenceDpodlCheckpointCID.
        if (bytes(expectedReferenceDpodlCheckpointCID).length == 0) {
            if (bytes(_referenceDpodlCheckpointCID).length != 0) {
                revert InvalidReferenceModel(_referenceDpodlCheckpointCID, "expected empty genesis reference DPoDL CID");
            }
            // If both are empty, it's a valid reference to genesis without a DPoDL checkpoint. Carry on.
        } else {
            if (keccak256(abi.encodePacked(_referenceDpodlCheckpointCID)) != keccak256(abi.encodePacked(expectedReferenceDpodlCheckpointCID))) {
                revert InvalidReferenceModel(_referenceDpodlCheckpointCID, expectedReferenceDpodlCheckpointCID);
            }
        }

        // 2. Check if accuracy meets the threshold
        if (_accuracyBPS < tAccuracyThresholdBPS) {
            revert AccuracyThresholdNotMet(_accuracyBPS, tAccuracyThresholdBPS);
        }

        // 3. Check if the Post-Hash meets the T1 threshold (difficulty)
        if (_postHash >= t1Threshold) { // Note: Lower hash is better
            revert HashThresholdNotMet(_postHash, t1Threshold);
        }

        // 4. Check if training steps are within allowed range
        if (_steps < minTrainingSteps || _steps > maxTrainingSteps) {
            revert StepsOutOfRange(_steps, minTrainingSteps, maxTrainingSteps);
        }

        // 5. Verify sufficient improvement over reference model
        bool hasImprovedSufficiently = verifyModelImprovement(_accuracyBPS, _steps, _referenceDpodlCheckpointCID);
        if (!hasImprovedSufficiently) {
            // More specific error about which improvement failed can be thrown by verifyModelImprovement itself if it reverts.
            // If verifyModelImprovement returns false instead of reverting on specific failures:
            if (bytes(_referenceDpodlCheckpointCID).length > 0) {
                 uint256 refBlockHeight = dpodlCheckpointCIDToBlockHeight[_referenceDpodlCheckpointCID];
                 if (refBlockHeight > 0) { // Ensure it is a valid block reference
                    ModelBlock memory refBlock = modelBlocks[refBlockHeight];
                    if (_accuracyBPS < refBlock.accuracyBPS + minAccuracyImprovementBPS) {
                        revert InsufficientImprovement(_accuracyBPS, refBlock.accuracyBPS, minAccuracyImprovementBPS);
                    }
                    if (_steps < refBlock.steps + minStepImprovement) {
                        revert InsufficientTrainingSteps(_steps, refBlock.steps, minStepImprovement);
                    }
                }
            }
            revert("Insufficient improvement over reference model");
        }

        // --- Update State --- 
        currentBlockHeight++;
        uint256 blockTimestamp = block.timestamp;

        modelBlocks[currentBlockHeight] = ModelBlock({
            blockHeight: currentBlockHeight,
            modelStateCID: _newModelStateCID,          // Store new model state CID
            dpodlCheckpointCID: _newDpodlCheckpointCID, // Store new DPoDL checkpoint CID
            accuracyBPS: _accuracyBPS,
            steps: _steps,
            postHash: _postHash,
            referenceModelCID: _referenceDpodlCheckpointCID, // Store the DPoDL checkpoint CID of the reference
            proposer: msg.sender,
            timestamp: blockTimestamp
        });

        // Map the new DPoDL checkpoint CID to the new block height
        dpodlCheckpointCIDToBlockHeight[_newDpodlCheckpointCID] = currentBlockHeight;

        // Update current global CIDs to reflect this new block
        currentModelStateCID = _newModelStateCID;
        currentDpodlCheckpointCID = _newDpodlCheckpointCID;

        // --- Emit Event ---
        emit ModelAccepted(
            currentBlockHeight,
            _newModelStateCID,       // Pass new model state CID
            _newDpodlCheckpointCID, // Pass new DPoDL checkpoint CID
            _accuracyBPS,
            _postHash,
            _referenceDpodlCheckpointCID, // Pass reference DPoDL checkpoint CID
            msg.sender,
            blockTimestamp
        );

        emit GlobalReferenceModelUpdated(
            currentModelStateCID, 
            currentDpodlCheckpointCID, 
            msg.sender, 
            currentBlockHeight, // ID is the block height
            true                // isBlockUpdate = true
        );

        // --- Reward Proposer & Reference --- 
        if (address(dpdlToken) != address(0) && blockRewardAmount > 0) {
            uint256 proposerReward = blockRewardAmount;
            uint256 referenceReward = 0;
            address referenceProposer = address(0);

            // Check if there's a reference DPoDL checkpoint and a share to distribute
            if (bytes(_referenceDpodlCheckpointCID).length > 0 && referenceRewardShareBPS > 0) {
                // Get the block height of the reference DPoDL checkpoint
                uint256 referenceBlockHeight = dpodlCheckpointCIDToBlockHeight[_referenceDpodlCheckpointCID];
                
                // Ensure reference block exists and has a proposer
                if (referenceBlockHeight > 0 && modelBlocks[referenceBlockHeight].proposer != address(0)) {
                    referenceProposer = modelBlocks[referenceBlockHeight].proposer;
                    
                    if (referenceProposer != msg.sender) {
                        referenceReward = (blockRewardAmount * referenceRewardShareBPS) / 10000;
                        proposerReward = blockRewardAmount - referenceReward;
                    } else {
                         referenceProposer = address(0); // Proposer is same as reference, gets full reward
                    }
                }
            }

            // Mint proposer reward
            try DPoDLToken(address(dpdlToken)).mint(msg.sender, proposerReward) {
                // Proposer reward successfully minted
            } catch {
                // Proposer minting failed. Treat as critical failure?
                // revert RewardMintFailed(); 
                 // Or just log and skip rewards?
                emit RewardMintFailed(msg.sender, proposerReward);
            }

            // Mint reference reward (if applicable)
            if (referenceProposer != address(0) && referenceReward > 0) {
                try DPoDLToken(address(dpdlToken)).mint(referenceProposer, referenceReward) {
                    // Reference reward successfully minted
                } catch {
                    // Reference minting failed. Log and continue.
                    emit RewardMintFailed(referenceProposer, referenceReward);
                }
            }
        }
    }

    /**
     * @notice Updates the global reference model CIDs from a selected Model Transaction (MTX).
     * @dev Callable only by the owner (or a designated operator in a future enhancement).
     *      This function assumes the MTX has been validated off-chain.
     *      It updates the current model state and DPoDL checkpoint CIDs,
     *      and calls the MTXMempool contract to mark the MTX as Processed.
     * @param _newModelStateCID The IPFS CID of the actual model state from the selected MTX.
     * @param _newDpodlCheckpointCID The IPFS CID of the D-PoDL checkpoint data from the selected MTX.
     * @param _mtxId The ID of the MTX in the MTXMempool.
     */
    function updateReferenceModelFromMtx(
        string memory _newModelStateCID,
        string memory _newDpodlCheckpointCID,
        uint256 _mtxId
    ) external onlyOwner returns (bool) {
        emit UpdateReferenceModelFromMtxCalled(_mtxId, _newModelStateCID, _newDpodlCheckpointCID, msg.sender);
        
        require(address(mtxMempoolContract) != address(0), "MR_ERR: Mempool contract address is zero");
        require(address(dpdlToken) != address(0), "MR_ERR: Token contract address is zero");

        // Correctly get the struct and then access its members
        MTXMempool.ModelTransaction memory mtx = mtxMempoolContract.getMtxDetails(_mtxId);

        require(mtx.mtxId == _mtxId, "MR_ERR: MTX ID mismatch or MTX not found");
        require(mtx.status == MTXMempool.Status.SelectedForProcessing, "MR_ERR: MTX not SelectedForProcessing"); // Use MTXMempool.Status
        require(bytes(mtx.ipfsCID).length > 0, "MR_ERR: MTX DPoDL Checkpoint CID is empty");
        require(bytes(_newModelStateCID).length > 0, "MR_ERR: New Model State CID is empty");
        require(keccak256(bytes(mtx.ipfsCID)) == keccak256(bytes(_newDpodlCheckpointCID)), "MR_ERR: DPoDL CIDs mismatch");

        currentModelStateCID = _newModelStateCID;
        currentDpodlCheckpointCID = _newDpodlCheckpointCID;
        lastGlobalModelUpdateTime = block.timestamp; // CORRECTED: Assignment to declared variable
        lastProcessedMtxId = _mtxId;                 // CORRECTED: Assignment to declared variable

        uint256 rewardAmount = mtxRewardAmount; // CORRECTED: Use state variable mtxRewardAmount
        if (rewardAmount > 0) {
            // CORRECTED: Cast to DPoDLToken (imported type) instead of undefined IDPoDLToken
            DPoDLToken(address(dpdlToken)).mint(mtx.submitter, rewardAmount);
            // The line above will revert if minting fails (e.g., due to lack of MINTER_ROLE)
            
            // CORRECTED: Use existing RewardDistributedForMtx event
            emit RewardDistributedForMtx(_mtxId, mtx.submitter, rewardAmount); 
        }

        mtxMempoolContract.updateMtxStatus(_mtxId, MTXMempool.Status.Processed); // Use MTXMempool.Status
        // CORRECTED: Use existing GlobalReferenceModelUpdated event with appropriate parameters for MTX update
        emit GlobalReferenceModelUpdated(
            _newModelStateCID, 
            _newDpodlCheckpointCID, 
            msg.sender, // The operator (owner) is the updater
            _mtxId,     // ID is the mtxId
            false       // isBlockUpdate = false for MTX
        );
        
        return true;
    }

    // --- View Functions ---

    /**
     * @dev OLD FUNCTION - Deprecated. Use getCurrentReferenceModelStateCID() instead.
     * Returns the IPFS CID of the latest accepted model block's primary CID (now modelStateCID).
     * Or returns the currentModelStateCID if no blocks have been added yet (genesis).
     */
    function getCurrentReferenceModel() public view returns (string memory) {
        // This function is kept for a brief period for compatibility if anything external still uses it,
        // but it should be considered deprecated in favor of the more specific CIDs.
        return currentModelStateCID;
    }

    /**
     * @notice Gets the IPFS CID of the current reference model's STATE (the weights, etc.).
     *         This is the model state that new training should be based on.
     */
    function getCurrentReferenceModelStateCID() public view returns (string memory) {
        return currentModelStateCID;
    }

    /**
     * @notice Gets the IPFS CID of the D-PoDL checkpoint data associated with the current reference model state.
     *         This checkpoint contains proofs, accuracy, and other metadata for the currentModelStateCID.
     *         May be an empty string if not applicable (e.g. for an initial genesis model without a DPoDL checkpoint).
     */
    function getCurrentReferenceDpodlCheckpointCID() public view returns (string memory) {
        return currentDpodlCheckpointCID;
    }

    /**
     * @dev Returns the details of a specific model block by its height.
     */
    function getBlockDetails(uint256 _blockHeight) public view returns (ModelBlock memory) {
        return modelBlocks[_blockHeight];
    }

    /**
     * @dev Returns the block height for a given IPFS CID, or 0 if not found.
     */
    function getBlockHeightForCID(string memory _dpodlCheckpointCID) public view returns (uint256) {
        return dpodlCheckpointCIDToBlockHeight[_dpodlCheckpointCID];
    }

    // --- Parameter Update Functions (Owner Controlled) ---

    /**
     * @dev Updates the T1 hash threshold. Only callable by the owner.
     * @param _newThreshold The new T1 threshold value.
     */
    function setT1Threshold(uint256 _newThreshold) public onlyOwner {
        t1Threshold = _newThreshold;
        emit ParameterUpdated("t1Threshold", _newThreshold);
    }

    /**
     * @dev Updates the accuracy threshold (in BPS). Only callable by the owner.
     * @param _newThresholdBPS The new accuracy threshold in Basis Points (1-10000).
     */
    function setTAccuracyThresholdBPS(uint256 _newThresholdBPS) public onlyOwner {
        if (_newThresholdBPS > 10000) revert("Accuracy BPS cannot exceed 10000"); 
        tAccuracyThresholdBPS = _newThresholdBPS;
        emit ParameterUpdated("tAccuracyThresholdBPS", _newThresholdBPS);
    }

    /**
     * @dev Updates the block reward amount. Only callable by the owner.
     * @param _newRewardAmount The new reward amount per block.
     */
    function setBlockRewardAmount(uint256 _newRewardAmount) public onlyOwner {
        blockRewardAmount = _newRewardAmount;
        emit ParameterUpdated("blockRewardAmount", _newRewardAmount);
    }

    /**
     * @dev Updates the minimum training steps required. Only callable by the owner.
     * @param _newMinSteps The new minimum training steps required.
     */
    function setMinTrainingSteps(uint256 _newMinSteps) public onlyOwner {
        if (_newMinSteps > maxTrainingSteps) revert("Min steps cannot exceed max steps");
        minTrainingSteps = _newMinSteps;
        emit ParameterUpdated("minTrainingSteps", _newMinSteps);
    }

    /**
     * @dev Updates the maximum training steps allowed. Only callable by the owner.
     * @param _newMaxSteps The new maximum training steps allowed.
     */
    function setMaxTrainingSteps(uint256 _newMaxSteps) public onlyOwner {
        if (_newMaxSteps < minTrainingSteps) revert("Max steps cannot be less than min steps");
        maxTrainingSteps = _newMaxSteps;
        emit ParameterUpdated("maxTrainingSteps", _newMaxSteps);
    }

    /**
     * @dev Updates the minimum required accuracy improvement over reference model.
     * @param _newMinImprovement The new minimum improvement in basis points.
     */
    function setMinAccuracyImprovementBPS(uint256 _newMinImprovement) public onlyOwner {
        minAccuracyImprovementBPS = _newMinImprovement;
        emit ParameterUpdated("minAccuracyImprovementBPS", _newMinImprovement);
    }

    /**
     * @dev Updates the minimum required step increase over reference model.
     * @param _newMinStepImprovement The new minimum step improvement required.
     */
    function setMinStepImprovement(uint256 _newMinStepImprovement) public onlyOwner {
        minStepImprovement = _newMinStepImprovement;
        emit ParameterUpdated("minStepImprovement", _newMinStepImprovement);
    }

    /**
     * @dev Updates the reference reward share (in BPS). Only callable by the owner.
     * @param _newShareBPS The new reference reward share in Basis Points (0-10000).
     */
    function setReferenceRewardShareBPS(uint256 _newShareBPS) public onlyOwner {
        if (_newShareBPS > 10000) revert("Reference reward share BPS cannot exceed 10000");
        referenceRewardShareBPS = _newShareBPS;
        emit ParameterUpdated("referenceRewardShareBPS", _newShareBPS);
    }

    /**
     * @dev Sets the DPDL token contract address. Only callable by the owner.
     * @param _newTokenAddress The address of the token contract.
     */
    function setDpdlToken(address _newTokenAddress) public onlyOwner {
        if (_newTokenAddress == address(0)) revert ZeroAddress();
        dpdlToken = IERC20(_newTokenAddress);
        emit ParameterUpdated("dpdlToken", uint256(uint160(_newTokenAddress))); // Emit address as uint
    }

    // --- Setter for MTXMempool Contract Address ---
    /**
     * @dev Sets the address of the MTXMempool contract.
     *      Only callable by the owner.
     * @param _mtxMempoolAddress The address of the MTXMempool contract.
     */
    function setMtxMempoolContract(address _mtxMempoolAddress) external onlyOwner {
        if (_mtxMempoolAddress == address(0)) revert ZeroAddress();
        mtxMempoolContract = IMTXMempool(_mtxMempoolAddress);
        // Optionally emit an event here if needed, e.g.:
        // emit ContractAddressUpdated("MTXMempool", _mtxMempoolAddress);
    }

    /**
     * @dev Updates the MTX reward amount. Only callable by the owner.
     * @param _newRewardAmount The new reward amount per processed MTX.
     */
    function setMtxRewardAmount(uint256 _newRewardAmount) public onlyOwner {
        mtxRewardAmount = _newRewardAmount;
        emit ParameterUpdated("mtxRewardAmount", _newRewardAmount);
    }
} 