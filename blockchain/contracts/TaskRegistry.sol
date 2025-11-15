// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title TaskRegistry
 * @dev Manages the lifecycle of AI training tasks submitted to the network.
 */
contract TaskRegistry is Ownable {
    // --- Enums ---

    enum TaskStatus {
        Pending,
        Active,
        Completed,
        Cancelled
    }

    // --- Structs ---

    /**
     * @dev Represents a single AI task defined by a publisher.
     */
    struct Task {
        uint256 taskId;                 // Unique ID for the task
        address publisher;              // Address that submitted the task
        string datasetIdentifier;       // e.g., IPFS CID or dataset name
        string evaluationCriteria;      // Description or identifier for the evaluation metric
        uint256 targetAccuracyBPS;      // Required accuracy in Basis Points (e.g., 9500 for 95.00%)
        uint256 rewardPool;             // Total reward allocated for completing the task (in DPDLToken units)
        uint256 taskDurationSeconds;    // Maximum duration allowed for the task
        TaskStatus status;              // Current status of the task
        uint256 submissionTimestamp;    // When the task was submitted
        uint256 startTimestamp;         // When the task became active
        uint256 endTimestamp;           // When the task was completed or cancelled
        string[] associatedModelCIDs;   // Models submitted against this task (optional)
    }

    // --- State Variables ---

    uint256 private _taskIds; // Use standard uint256 for task ID counter
    mapping(uint256 => Task) public tasks; // taskId => Task data
    mapping(address => uint256[]) public tasksByPublisher; // publisher address => list of task IDs
    mapping(TaskStatus => uint256[]) public tasksByStatus; // status => list of task IDs (Careful: managing removals can be complex/costly)
    // TODO: Consider if tasksByStatus is necessary due to potential gas costs on status change. Events might be better.

    // --- Events ---

    event TaskSubmitted(
        uint256 indexed taskId,
        address indexed publisher,
        string datasetIdentifier,
        uint256 targetAccuracyBPS,
        uint256 rewardPool,
        uint256 taskDurationSeconds
    );

    event TaskStatusUpdated(
        uint256 indexed taskId,
        TaskStatus newStatus,
        uint256 timestamp
    );

    event ModelAssociatedToTask(
        uint256 indexed taskId,
        string modelCID
    );

    // --- Errors ---

    error InvalidTaskId(uint256 taskId);
    error InvalidTaskStatusTransition(uint256 taskId, TaskStatus currentStatus, TaskStatus requestedStatus);
    error TaskAlreadyStarted(uint256 taskId);
    error TaskNotActive(uint256 taskId);
    error Unauthorized(); // For actions restricted to publisher or owner

    // --- Constructor ---

    constructor(address initialOwner) Ownable(initialOwner) {}

    // --- Functions ---

    /**
     * @dev Allows anyone (or restrict with roles later) to submit a new task.
     */
    function submitTask(
        string memory _datasetIdentifier,
        string memory _evaluationCriteria,
        uint256 _targetAccuracyBPS,
        uint256 _rewardPool, // Assumes reward is pre-funded or handled externally
        uint256 _taskDurationSeconds
    ) public returns (uint256) {
        _taskIds++; // Manually increment the counter
        uint256 newTaskId = _taskIds; // Assign the new ID

        tasks[newTaskId] = Task({
            taskId: newTaskId,
            publisher: msg.sender,
            datasetIdentifier: _datasetIdentifier,
            evaluationCriteria: _evaluationCriteria,
            targetAccuracyBPS: _targetAccuracyBPS,
            rewardPool: _rewardPool,
            taskDurationSeconds: _taskDurationSeconds,
            status: TaskStatus.Pending,
            submissionTimestamp: block.timestamp,
            startTimestamp: 0,
            endTimestamp: 0,
            associatedModelCIDs: new string[](0)
        });

        tasksByPublisher[msg.sender].push(newTaskId);
        // tasksByStatus[TaskStatus.Pending].push(newTaskId); // Manage complexity if needed

        emit TaskSubmitted(
            newTaskId,
            msg.sender,
            _datasetIdentifier,
            _targetAccuracyBPS,
            _rewardPool,
            _taskDurationSeconds
        );

        return newTaskId;
    }

    /**
     * @dev Allows the owner to activate a pending task.
     */
    function startTask(uint256 _taskId) public onlyOwner {
        Task storage task = tasks[_taskId];
        if (task.taskId == 0) revert InvalidTaskId(_taskId); // Check existence
        if (task.status != TaskStatus.Pending) revert InvalidTaskStatusTransition(_taskId, task.status, TaskStatus.Active);

        task.status = TaskStatus.Active;
        task.startTimestamp = block.timestamp;

        // Update tasksByStatus if implemented
        // _removeTaskFromStatusList(TaskStatus.Pending, _taskId);
        // tasksByStatus[TaskStatus.Active].push(_taskId);

        emit TaskStatusUpdated(_taskId, TaskStatus.Active, block.timestamp);
    }

     /**
     * @dev Allows the owner or publisher to mark an active task as completed.
     * Note: Reward distribution logic is NOT handled here.
     */
    function completeTask(uint256 _taskId) public {
        Task storage task = tasks[_taskId];
        if (task.taskId == 0) revert InvalidTaskId(_taskId);
        // Allow owner or original publisher to complete
        if (msg.sender != owner() && msg.sender != task.publisher) revert Unauthorized();
        if (task.status != TaskStatus.Active) revert InvalidTaskStatusTransition(_taskId, task.status, TaskStatus.Completed);

        task.status = TaskStatus.Completed;
        task.endTimestamp = block.timestamp;

        // Update tasksByStatus if implemented
        // _removeTaskFromStatusList(TaskStatus.Active, _taskId);
        // tasksByStatus[TaskStatus.Completed].push(_taskId);

        emit TaskStatusUpdated(_taskId, TaskStatus.Completed, block.timestamp);
    }

    /**
     * @dev Allows the owner or publisher to cancel a pending or active task.
     */
    function cancelTask(uint256 _taskId) public {
        Task storage task = tasks[_taskId];
        if (task.taskId == 0) revert InvalidTaskId(_taskId);
         // Allow owner or original publisher to cancel
        if (msg.sender != owner() && msg.sender != task.publisher) revert Unauthorized();
        if (task.status != TaskStatus.Pending && task.status != TaskStatus.Active) {
             revert InvalidTaskStatusTransition(_taskId, task.status, TaskStatus.Cancelled);
        }

        task.status = TaskStatus.Cancelled;
        task.endTimestamp = block.timestamp;

        // Update tasksByStatus if implemented
        // _removeTaskFromStatusList(previousStatus, _taskId);
        // tasksByStatus[TaskStatus.Cancelled].push(_taskId);

        emit TaskStatusUpdated(_taskId, TaskStatus.Cancelled, block.timestamp);
    }

    /**
     * @dev Associates a model CID with a specific task. Can be called internally or by other contracts.
     * Typically called when a model is submitted to ModelRegistry referencing this task.
     * Restricted to owner to prevent unauthorized model associations.
     */
    function associateModelToTask(uint256 _taskId, string memory _modelCID) external onlyOwner {
        Task storage task = tasks[_taskId];
        if (task.taskId == 0) revert InvalidTaskId(_taskId);
        // Potentially check if task is Active?
        // if (task.status != TaskStatus.Active) revert TaskNotActive(_taskId);

        task.associatedModelCIDs.push(_modelCID);
        emit ModelAssociatedToTask(_taskId, _modelCID);
    }


    // --- View Functions ---

    function getTaskDetails(uint256 _taskId) public view returns (Task memory) {
        if (tasks[_taskId].taskId == 0) revert InvalidTaskId(_taskId);
        return tasks[_taskId];
    }

    function getPublisherTasks(address _publisher) public view returns (uint256[] memory) {
        return tasksByPublisher[_publisher];
    }

     function getTaskCount() public view returns (uint256) {
        return _taskIds; // Return the uint256 value directly
    }

    // --- Internal Helper Functions ---

    // Helper function to remove task from status list (if tasksByStatus is used)
    // function _removeTaskFromStatusList(TaskStatus status, uint256 taskIdToRemove) internal {
    //     uint256[] storage taskList = tasksByStatus[status];
    //     for (uint i = 0; i < taskList.length; i++) {
    //         if (taskList[i] == taskIdToRemove) {
    //             taskList[i] = taskList[taskList.length - 1];
    //             taskList.pop();
    //             break;
    //         }
    //     }
    // }

} 