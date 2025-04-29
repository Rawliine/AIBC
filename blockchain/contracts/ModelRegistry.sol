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

    // --- Errors ---
    error InvalidReferenceModel(string submittedCID, string expectedCID);
    error HashThresholdNotMet(uint256 submittedHash, uint256 threshold);
    error AccuracyThresholdNotMet(uint256 submittedAccuracyBPS, uint256 thresholdBPS);
    error InvalidTokenAddress();
    error RewardMintFailed();
    error ZeroAddress();
    error ZeroValue();

    // --- Constructor ---

    /**
     * @dev Initializes the contract, setting D-PoDL parameters and the token address.
     * @param _initialT1Threshold The initial T1 hash difficulty threshold.
     * @param _initialTAccuracyThresholdBPS The initial accuracy threshold in Basis Points (1-10000).
     * @param _initialBlockRewardAmount The initial DPDL token reward per accepted block.
     * @param _tokenAddress The address of the deployed DPoDLToken contract.
     * @param _initialOwner The address designated as the contract owner.
     */
    constructor(
        uint256 _initialT1Threshold,
        uint256 _initialTAccuracyThresholdBPS,
        uint256 _initialBlockRewardAmount,
        address _tokenAddress,
        address _initialOwner // Pass initial owner explicitly
    ) Ownable(_initialOwner) { // Initialize Ownable with the owner
        if (_tokenAddress == address(0)) revert ZeroAddress();
        if (_initialOwner == address(0)) revert ZeroAddress(); // Ensure owner is not zero address
        // Basic sanity check for accuracy threshold (e.g., between 0% and 100%)
        if (_initialTAccuracyThresholdBPS > 10000) revert("Accuracy BPS cannot exceed 10000"); 

        t1Threshold = _initialT1Threshold;
        tAccuracyThresholdBPS = _initialTAccuracyThresholdBPS;
        blockRewardAmount = _initialBlockRewardAmount;
        dpdlToken = IERC20(_tokenAddress);
        currentBlockHeight = 0; // Initialize block height

        emit ParameterUpdated("t1Threshold", _initialT1Threshold);
        emit ParameterUpdated("tAccuracyThresholdBPS", _initialTAccuracyThresholdBPS);
        emit ParameterUpdated("blockRewardAmount", _initialBlockRewardAmount);
        emit ParameterUpdated("dpdlToken", uint256(uint160(_tokenAddress))); // Emit address as uint
    }

    // --- Core Functions ---

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

        // --- Reward Proposer ---
        // Attempt to mint tokens directly to the proposer via the DPoDLToken contract.
        // This requires that this ModelRegistry contract's owner (or potentially the 
        // contract itself, depending on DPoDLToken access control) has minting
        // privileges on the DPoDLToken contract.
        if (address(dpdlToken) != address(0) && blockRewardAmount > 0) {
            try DPoDLToken(address(dpdlToken)).mint(msg.sender, blockRewardAmount) {
                // Reward successfully minted
            } catch {
                // Minting failed. Could be due to lack of permissions, token pausing, etc.
                // In a production system, you might want to log this failure off-chain
                // or implement a fallback reward mechanism. For now, we proceed without reward.
                // Uncomment the line below to make reward mandatory for block acceptance.
                // revert RewardMintFailed(); 
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
     * @dev Updates the target accuracy threshold (in Basis Points).
     *      Only callable by the owner.
     * @param _newThresholdBPS The new accuracy threshold (1-10000).
     */
    function setTAccuracyThresholdBPS(uint256 _newThresholdBPS) public onlyOwner {
        // Basic sanity check
        if (_newThresholdBPS > 10000) revert("Accuracy BPS cannot exceed 10000"); 
        tAccuracyThresholdBPS = _newThresholdBPS;
        emit ParameterUpdated("tAccuracyThresholdBPS", _newThresholdBPS);
    }

    /**
     * @dev Updates the block reward amount. Only callable by the owner.
     * @param _newRewardAmount The new reward amount in DPDL tokens (smallest unit).
     */
    function setBlockRewardAmount(uint256 _newRewardAmount) public onlyOwner {
        blockRewardAmount = _newRewardAmount;
        emit ParameterUpdated("blockRewardAmount", _newRewardAmount);
    }

    /**
     * @dev Updates the address of the DPoDLToken contract. Only callable by the owner.
     * @param _newTokenAddress The new address of the token contract.
     */
    function setTokenAddress(address _newTokenAddress) public onlyOwner {
        if (_newTokenAddress == address(0)) revert ZeroAddress();
        dpdlToken = IERC20(_newTokenAddress);
        emit ParameterUpdated("dpdlToken", uint256(uint160(_newTokenAddress)));
    }

} 