// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol"; // Interface for interacting with the token
import "./DPoDLToken.sol"; // Import the specific token contract type

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
        string ipfsCID;               // IPFS CID of the model checkpoint file
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
    uint256 public blockRewardAmount;   // Amount of DPDL tokens rewarded per block
    uint256 public minTrainingSteps;    // Minimum training steps required
    uint256 public maxTrainingSteps;    // Maximum training steps allowed to prevent overtraining
    uint256 public referenceRewardShareBPS; // Share of reward for reference model proposer (0-10000)

    // Additional state variables for model improvement verification
    uint256 public minAccuracyImprovementBPS; // Minimum accuracy improvement in BPS
    uint256 public minStepImprovement;         // Minimum additional steps required

    // Token Contract
    IERC20 public dpdlToken;             // Address of the DPoDLToken contract

    // Model Chain Storage
    mapping(uint256 => ModelBlock) public modelBlocks; // blockHeight => ModelBlock data
    uint256 public currentBlockHeight;                 // Height of the latest accepted block
    mapping(string => uint256) public cidToBlockHeight; // ipfsCID => blockHeight (for quick lookup)

    // Genesis Block Info (optional, can be set in constructor or first submission)
    string public genesisCID = ""; // Placeholder for potential genesis model

    // --- Events ---

    /**
     * @dev Emitted when a new model block is successfully validated and added to the registry.
     */
    event ModelAccepted(
        uint256 indexed blockHeight,
        string ipfsCID,
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
    event RewardMintFailed(address indexed proposer, uint256 amount);

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
        address _initialOwner // Pass initial owner explicitly
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

        emit ParameterUpdated("t1Threshold", _initialT1Threshold);
        emit ParameterUpdated("tAccuracyThresholdBPS", _initialTAccuracyThresholdBPS);
        emit ParameterUpdated("blockRewardAmount", _initialBlockRewardAmount);
        emit ParameterUpdated("minTrainingSteps", _initialMinTrainingSteps);
        emit ParameterUpdated("maxTrainingSteps", _initialMaxTrainingSteps);
        emit ParameterUpdated("minAccuracyImprovementBPS", _initialMinAccuracyImprovementBPS);
        emit ParameterUpdated("minStepImprovement", _initialMinStepImprovement);
        emit ParameterUpdated("referenceRewardShareBPS", _initialReferenceRewardShareBPS);
        emit ParameterUpdated("dpdlToken", uint256(uint160(_tokenAddress))); // Emit address as uint
    }

    // --- Core Functions ---

    /**
     * @dev Verifies that a model has made sufficient improvement over its reference model.
     * @param _accuracyBPS The accuracy of the submitted model.
     * @param _steps The training steps of the submitted model.
     * @param _referenceModelCID The CID of the reference model.
     * @return A boolean indicating if the improvement is sufficient.
     */
    function verifyModelImprovement(
        uint256 _accuracyBPS,
        uint256 _steps,
        string memory _referenceModelCID
    ) public view returns (bool) {
        // Skip improvement check for genesis submissions
        if (bytes(_referenceModelCID).length == 0 || 
            keccak256(abi.encodePacked(_referenceModelCID)) == keccak256(abi.encodePacked(genesisCID))) {
            return true;
        }

        // Get reference model block height
        uint256 referenceBlockHeight = cidToBlockHeight[_referenceModelCID];
        if (referenceBlockHeight == 0) {
            // Reference model not found in registry
            return false;
        }

        // Get reference model details
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
     * @param _ipfsCID The IPFS CID of the proposed model checkpoint.
     * @param _accuracyBPS The accuracy achieved by the model (in Basis Points, 1-10000).
     * @param _steps The number of training steps performed.
     * @param _postHash The Post-Hash value calculated by the worker.
     * @param _referenceModelCID The CID of the model this submission was based on.
     */
    function submitBlock(
        string memory _ipfsCID,
        uint256 _accuracyBPS,
        uint256 _steps,
        uint256 _postHash,
        string memory _referenceModelCID
    ) public {
        // --- Validation Checks ---

        // 1. Check if based on the correct reference model (current chain head)
        string memory expectedReferenceCID = getCurrentReferenceModel();
        // Use keccak256 for string comparison as Solidity lacks direct `==` for strings in storage/memory
        if (keccak256(abi.encodePacked(_referenceModelCID)) != keccak256(abi.encodePacked(expectedReferenceCID))) {
            revert InvalidReferenceModel(_referenceModelCID, expectedReferenceCID);
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
        bool hasImprovedSufficiently = verifyModelImprovement(_accuracyBPS, _steps, _referenceModelCID);
        if (!hasImprovedSufficiently) {
            // Check exactly which improvement criterion failed
            if (bytes(_referenceModelCID).length > 0 && 
                keccak256(abi.encodePacked(_referenceModelCID)) != keccak256(abi.encodePacked(genesisCID))) {
                uint256 referenceBlockHeight = cidToBlockHeight[_referenceModelCID];
                if (referenceBlockHeight > 0) {
                    ModelBlock memory referenceBlock = modelBlocks[referenceBlockHeight];
                    
                    if (_accuracyBPS < referenceBlock.accuracyBPS + minAccuracyImprovementBPS) {
                        revert InsufficientImprovement(_accuracyBPS, referenceBlock.accuracyBPS, minAccuracyImprovementBPS);
                    }
                    
                    if (_steps < referenceBlock.steps + minStepImprovement) {
                        revert InsufficientTrainingSteps(_steps, referenceBlock.steps, minStepImprovement);
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
            ipfsCID: _ipfsCID,
            accuracyBPS: _accuracyBPS,
            steps: _steps,
            postHash: _postHash,
            referenceModelCID: _referenceModelCID, // Storing the reference used
            proposer: msg.sender,                  // The address calling this function
            timestamp: blockTimestamp
        });

        cidToBlockHeight[_ipfsCID] = currentBlockHeight;

        // --- Emit Event ---
        emit ModelAccepted(
            currentBlockHeight,
            _ipfsCID,
            _accuracyBPS,
            _postHash,
            _referenceModelCID,
            msg.sender,
            blockTimestamp
        );

        // --- Reward Proposer & Reference --- 
        if (address(dpdlToken) != address(0) && blockRewardAmount > 0) {
            uint256 proposerReward = blockRewardAmount;
            uint256 referenceReward = 0;
            address referenceProposer = address(0);

            // Check if there's a reference and a share to distribute
            if (bytes(_referenceModelCID).length > 0 && 
                keccak256(abi.encodePacked(_referenceModelCID)) != keccak256(abi.encodePacked(genesisCID)) && 
                referenceRewardShareBPS > 0)
            {
                uint256 referenceBlockHeight = cidToBlockHeight[_referenceModelCID];
                // Ensure reference block exists and has a proposer
                if (referenceBlockHeight > 0 && modelBlocks[referenceBlockHeight].proposer != address(0)) {
                    referenceProposer = modelBlocks[referenceBlockHeight].proposer;
                    
                    // Avoid giving reference reward if proposer is the same as reference proposer
                    if (referenceProposer != msg.sender) {
                        referenceReward = (blockRewardAmount * referenceRewardShareBPS) / 10000;
                        proposerReward = blockRewardAmount - referenceReward;
                    } else {
                         // Proposer is same as reference, gets full reward
                         // referenceProposer remains address(0) for minting logic
                         referenceProposer = address(0);
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

    // --- View Functions ---

    /**
     * @dev Returns the IPFS CID of the latest accepted model block.
     *      Returns the genesisCID if no blocks have been added yet.
     */
    function getCurrentReferenceModel() public view returns (string memory) {
        if (currentBlockHeight == 0) {
            return genesisCID; // Or revert if genesis must be explicitly set
        }
        return modelBlocks[currentBlockHeight].ipfsCID;
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
    function getBlockHeightForCID(string memory _ipfsCID) public view returns (uint256) {
        return cidToBlockHeight[_ipfsCID];
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

    /**
     * @dev Sets the genesis model CID, which can only be set once when empty.
     * @param _genesisCID The IPFS CID of the genesis model.
     */
    function setGenesisCID(string memory _genesisCID) public onlyOwner {
        if (bytes(genesisCID).length > 0) revert("Genesis CID already set");
        if (bytes(_genesisCID).length == 0) revert("Genesis CID cannot be empty");
        genesisCID = _genesisCID;
    }
} 