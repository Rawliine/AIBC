// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MTXMempool
 * @dev Manages the mempool for Model Transactions (MTX) - proposed models
 *      that haven't necessarily met block acceptance criteria (T1/T_acc)
 *      but might be used as starting points (reference models) for future work.
 */
contract MTXMempool is Ownable {

    // --- Structs ---

    /**
     * @dev Represents a single Model Transaction (MTX) in the mempool.
     */
    struct ModelTransaction {
        uint256 mtxId;                // Unique ID for the MTX
        string ipfsCID;               // IPFS CID of the model checkpoint file
        uint256 accuracyBPS;          // Accuracy in Basis Points (e.g., 8500 for 85.00%)
        uint256 steps;                // Training steps performed for this model
        string referenceModelCID;     // CID of the model this MTX was based on
        address submitter;            // Address that submitted this MTX
        uint256 timestamp;            // Timestamp when the MTX was submitted
        bool isValid;                 // Flag to indicate if the MTX exists (used for mapping checks)
    }

    // --- State Variables ---

    mapping(uint256 => ModelTransaction) public mtxPool; // mtxId => ModelTransaction data
    uint256 public nextMtxId;                          // Counter for assigning unique IDs

    // Optional: Add limits or cleanup mechanisms if needed (e.g., max size, TTL)
    // uint256 public maxMempoolSize = 1000;
    // mapping(uint256 => bool) public activeMtxIds; // Alternative tracking

    // --- Events ---

    /**
     * @dev Emitted when a new MTX is added to the mempool.
     */
    event MtxSubmitted(
        uint256 indexed mtxId,
        string ipfsCID,
        uint256 accuracyBPS,
        string referenceModelCID,
        address indexed submitter,
        uint256 timestamp
    );

    // --- Errors ---
    // (Add specific errors if needed, e.g., MempoolFull)
    error InvalidMtxId(uint256 mtxId);

    // --- Constructor ---
    constructor(address _initialOwner) Ownable(_initialOwner) {
        nextMtxId = 1; // Start MTX IDs from 1
    }

    // --- Core Functions ---

    /**
     * @dev Adds a new Model Transaction (MTX) to the mempool.
     *      Called by workers when they save an MTX checkpoint.
     * @param _ipfsCID The IPFS CID of the proposed model checkpoint.
     * @param _accuracyBPS The accuracy achieved by the model (in Basis Points).
     * @param _steps The number of training steps performed.
     * @param _referenceModelCID The CID of the model this MTX was based on.
     */
    function submitMtx(
        string memory _ipfsCID,
        uint256 _accuracyBPS,
        uint256 _steps,
        string memory _referenceModelCID
    ) public {
        // Basic validation (add more if needed, e.g., check string lengths)
        // require(bytes(_ipfsCID).length > 0, "IPFS CID cannot be empty");

        uint256 currentMtxId = nextMtxId;
        uint256 submissionTimestamp = block.timestamp;

        mtxPool[currentMtxId] = ModelTransaction({
            mtxId: currentMtxId,
            ipfsCID: _ipfsCID,
            accuracyBPS: _accuracyBPS,
            steps: _steps,
            referenceModelCID: _referenceModelCID,
            submitter: msg.sender,
            timestamp: submissionTimestamp,
            isValid: true
        });

        nextMtxId++;

        emit MtxSubmitted(
            currentMtxId,
            _ipfsCID,
            _accuracyBPS,
            _referenceModelCID,
            msg.sender,
            submissionTimestamp
        );

        // Optional: Implement mempool size management/cleanup logic here if needed
    }

    // --- View Functions ---

    /**
     * @dev Returns the details of a specific MTX by its ID.
     */
    function getMtxDetails(uint256 _mtxId) public view returns (ModelTransaction memory) {
        if (!mtxPool[_mtxId].isValid) {
             revert InvalidMtxId(_mtxId);
        }
        return mtxPool[_mtxId];
    }

    /**
     * @dev Returns the current total number of MTXs submitted (including potentially old ones).
     */
    function getMtxCount() public view returns (uint256) {
        return nextMtxId - 1;
    }

    // Note: Querying/filtering (e.g., finding all MTXs for a specific reference CID
    // or finding the highest accuracy MTX) is generally inefficient to do directly
    // on-chain within Solidity due to gas costs associated with iterating storage.
    // The typical pattern is:
    // 1. Emit detailed events (`MtxSubmitted`).
    // 2. Use an off-chain service (like The Graph, or a custom indexer) to listen
    //    to these events and build a queryable database.
    // 3. The Python trainer queries this off-chain service/database to find the
    //    best MTX candidate based on its criteria (e.g., highest accuracy for the
    //    current reference model).
    // We *could* add complex on-chain query functions, but they would be gas-intensive
    // and likely impractical for a large mempool.

} 