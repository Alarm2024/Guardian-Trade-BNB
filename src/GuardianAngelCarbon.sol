// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

/**
 * @notice Enterprise‑grade prize distribution protocol with multi‑role governance,
 *         timelocked parameter changes, carbon‑offset accounting, and oracle‑ready
 *         sustainability verification.
 */
contract GuardianAngelCarbon {

    // ================================================================
    // CUSTOM ERRORS
    // ================================================================
    error Unauthorized();
    error NotOwner();
    error NotGuardian();
    error NotVerifier();
    error NotPendingOwner();
    error ContractPaused();
    error NotPaused();
    error ZeroAddress();
    error NoChange();
    error InsufficientFunds();
    error TransferFailed();
    error InvalidAmount();
    error AwardNotFound();
    error AwardAlreadyVerified();
    error AwardAlreadyDistributed();
    error AwardNotVerified();
    error RecipientIsContractNotAllowed();
    error TimelockActive();
    error NoPendingChange();
    error ChangeNotApproved();
    error ChangeAlreadyExecuted();
    error InvalidBasisPoints();
    error ProposalNotFound();
    error ProposalAlreadyExecuted();
    error ProposalExpired();

    // ================================================================
    // EVENTS
    // ================================================================
    event OwnershipTransferStarted(address indexed previousOwner, address indexed newOwner);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event GuardianRotated(address indexed previous, address indexed newGuardian);
    event GuardianRotationCancelled(address indexed cancelledBy);
    event GuardianRotationInitiated(address indexed current, address indexed pending, uint256 unlockTime);
    event ChangeProposed(bytes32 indexed proposalId, address indexed proposer, uint256 deadline);
    event ChangeApproved(bytes32 indexed proposalId, address indexed approver);
    event ChangeExecuted(bytes32 indexed proposalId, bytes32 indexed parameter, uint256 value);
    event ChangeCancelled(bytes32 indexed proposalId, address indexed canceller);
    event Paused(address indexed triggeredBy);
    event Unpaused(address indexed triggeredBy);
    event AwardCreated(uint256 indexed awardId, address indexed recipient, uint256 amount, address indexed creator);
    event AwardVerified(uint256 indexed awardId, address indexed verifier);
    event AwardDistributed(uint256 indexed awardId, address indexed recipient, uint256 amount, uint256 offsetAmount, address indexed offsetRecipient);
    event OffsetRecipientUpdated(address indexed newRecipient);
    event OffsetBpsUpdated(uint256 newBps);
    event VerifierUpdated(address indexed newVerifier);
    event ETHReceived(address indexed from, uint256 amount);
    event AllowedContractUpdated(address indexed contractAddr, bool status);

    // ================================================================
    // CONSTANTS
    // ================================================================
    uint256 public constant CHANGE_TIMELOCK = 2 days;
    uint256 private constant MAX_BPS = 10000;

    // ================================================================
    // STATE VARIABLES
    // ================================================================
    address public owner;
    address public pendingOwner;
    address public guardian;
    address public pendingGuardian;
    uint256 public guardianRotationUnlock;
    address public verifier;
    address public offsetRecipient;
    uint256 public offsetBps;
    struct Award {
        address recipient;
        uint256 amount;
        bool verified;
        bool distributed;
        uint256 createdAt;
    }
    mapping(uint256 => Award) public awards;
    uint256 public awardCount;
    mapping(address => bool) public allowedContracts;
    bool public paused;
    uint256 private _reentrancyStatus;
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    struct Proposal {
        bytes32 parameter;
        uint256 value;
        uint256 deadline;
        bool executed;
        bool approvedByOwner;
        bool approvedByGuardian;
    }
    mapping(bytes32 => Proposal) public proposals;
    bytes32[] public proposalIds;

    // ================================================================
    // MODIFIERS
    // ================================================================
    modifier onlyOwner() { if (msg.sender != owner) revert NotOwner(); _; }
    modifier onlyGuardian() { if (msg.sender != guardian) revert NotGuardian(); _; }
    modifier onlyOwnerOrGuardian() { if (msg.sender != owner && msg.sender != guardian) revert Unauthorized(); _; }
    modifier onlyVerifier() { if (msg.sender != verifier) revert NotVerifier(); _; }
    modifier whenNotPaused() { if (paused) revert ContractPaused(); _; }
    modifier whenPaused() { if (!paused) revert NotPaused(); _; }
    modifier nonReentrant() { if (_reentrancyStatus == _ENTERED) revert Unauthorized(); _reentrancyStatus = _ENTERED; _; _reentrancyStatus = _NOT_ENTERED; }

    constructor(address initialGuardian, address initialVerifier, address initialOffsetRecipient, uint256 initialOffsetBps) {
        if (initialGuardian == address(0) || initialVerifier == address(0) || initialOffsetRecipient == address(0)) revert ZeroAddress();
        if (initialOffsetBps > MAX_BPS) revert InvalidBasisPoints();
        owner = msg.sender;
        guardian = initialGuardian;
        verifier = initialVerifier;
        offsetRecipient = initialOffsetRecipient;
        offsetBps = initialOffsetBps;
        _reentrancyStatus = _NOT_ENTERED;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert NotPendingOwner();
        owner = pendingOwner;
        pendingOwner = address(0);
        emit OwnershipTransferred(owner, pendingOwner);
    }

    function initiateGuardianRotation(address newGuardian) external onlyOwner {
        if (newGuardian == address(0)) revert ZeroAddress();
        pendingGuardian = newGuardian;
        guardianRotationUnlock = block.timestamp + 24 hours;
        emit GuardianRotationInitiated(guardian, newGuardian, guardianRotationUnlock);
    }

    function finalizeGuardianRotation() external onlyOwner {
        if (pendingGuardian == address(0)) revert NoChange();
        if (block.timestamp < guardianRotationUnlock) revert TimelockActive();
        guardian = pendingGuardian;
        pendingGuardian = address(0);
        guardianRotationUnlock = 0;
        emit GuardianRotated(guardian, pendingGuardian);
    }

    function pause() external onlyOwnerOrGuardian { paused = true; emit Paused(msg.sender); }
    function unpause() external onlyOwner { paused = false; emit Unpaused(msg.sender); }

    function createAward(address recipient, uint256 amount) external onlyGuardian whenNotPaused {
        if (recipient == address(0)) revert ZeroAddress();
        if (amount == 0) revert InvalidAmount();
        uint256 id = awardCount++;
        awards[id] = Award({recipient: recipient, amount: amount, verified: false, distributed: false, createdAt: block.timestamp});
        emit AwardCreated(id, recipient, amount, msg.sender);
    }

    function verifyAward(uint256 awardId) external onlyVerifier whenNotPaused {
        Award storage award = awards[awardId];
        if (award.recipient == address(0)) revert AwardNotFound();
        award.verified = true;
        emit AwardVerified(awardId, msg.sender);
    }

    function distributeAward(uint256 awardId) external nonReentrant whenNotPaused {
        Award storage award = awards[awardId];
        if (!award.verified) revert AwardNotVerified();
        if (award.distributed) revert AwardAlreadyDistributed();
        uint256 offsetAmount = (award.amount * offsetBps) / MAX_BPS;
        uint256 recipientAmount = award.amount - offsetAmount;
        award.distributed = true;
        if (offsetAmount > 0) payable(offsetRecipient).transfer(offsetAmount);
        payable(award.recipient).transfer(recipientAmount);
        emit AwardDistributed(awardId, award.recipient, award.amount, offsetAmount, offsetRecipient);
    }

    function propose(bytes32 parameter, uint256 value) external onlyOwnerOrGuardian {
        bytes32 proposalId = keccak256(abi.encode(parameter, value, block.timestamp, msg.sender));
        proposals[proposalId] = Proposal({
            parameter: parameter,
            value: value,
            deadline: block.timestamp + CHANGE_TIMELOCK,
            executed: false,
            approvedByOwner: msg.sender == owner,
            approvedByGuardian: msg.sender == guardian
        });
        proposalIds.push(proposalId);
        emit ChangeProposed(proposalId, msg.sender, proposals[proposalId].deadline);
    }

    function approveProposal(bytes32 proposalId) external onlyOwnerOrGuardian {
        Proposal storage proposal = proposals[proposalId];
        if (proposal.deadline == 0) revert ProposalNotFound();
        if (block.timestamp > proposal.deadline) revert ProposalExpired();
        if (msg.sender == owner) proposal.approvedByOwner = true;
        if (msg.sender == guardian) proposal.approvedByGuardian = true;
        emit ChangeApproved(proposalId, msg.sender);
    }
function executeProposal(bytes32 proposalId) external {
    Proposal storage proposal = proposals[proposalId];
    if (proposal.deadline == 0) revert ProposalNotFound();
    if (proposal.executed) revert ProposalAlreadyExecuted();
    if (!proposal.approvedByOwner || !proposal.approvedByGuardian) revert ChangeNotApproved();
    if (block.timestamp < proposal.deadline) revert TimelockActive();

    proposal.executed = true;

    if (proposal.parameter == keccak256("offsetBps")) {
        if (proposal.value > MAX_BPS) revert InvalidBasisPoints();
        offsetBps = proposal.value;
        emit ChangeExecuted(proposalId, proposal.parameter, proposal.value);
    } else if (proposal.parameter == keccak256("verifier")) {
        verifier = address(uint160(proposal.value));
        emit ChangeExecuted(proposalId, proposal.parameter, proposal.value);
    } else if (proposal.parameter == keccak256("offsetRecipient")) {
        offsetRecipient = address(uint160(proposal.value));
        emit ChangeExecuted(proposalId, proposal.parameter, proposal.value);
    } else {
        revert ProposalNotFound();
    }
}

receive() external payable { emit ETHReceived(msg.sender, msg.value); }
}

