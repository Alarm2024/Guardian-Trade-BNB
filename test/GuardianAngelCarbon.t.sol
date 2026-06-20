// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

import "forge-std/Test.sol";
import "../src/GuardianAngelCarbon.sol";

contract GuardianAngelCarbonTest is Test {
    GuardianAngelCarbon public gac;
    address public owner = address(1);
    address public guardian = address(2);
    address public verifier = address(3);
    address public offsetRecipient = address(4);

    function setUp() public {
        vm.prank(owner);
        gac = new GuardianAngelCarbon(guardian, verifier, offsetRecipient, 500);
    }

    function testProposalLifecycle() public {
        bytes32 param = keccak256("offsetBps");
        uint256 value = 1000;

        // Propose
        vm.prank(owner);
        gac.propose(param, value);
        
        // Need to find proposalId. Since it's calculated in propose, I need to know the inputs.
        // For testing, I'll use event to capture it.
        bytes32 proposalId = keccak256(abi.encode(param, value, block.timestamp, owner));

        // Approve by owner
        vm.prank(owner);
        gac.approveProposal(proposalId);
        
        // Approve by guardian
        vm.prank(guardian);
        gac.approveProposal(proposalId);
        
        // Advance time
        vm.warp(block.timestamp + 3 days);
        
        // Execute
        gac.executeProposal(proposalId);
        
        assertEq(gac.offsetBps(), value);
    }
}
