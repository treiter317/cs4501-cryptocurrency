// SPDX-License-Identifier: GPL-3.0-or-later

pragma solidity ^0.8.24;

import "./IGradebook.sol";

contract Gradebook is IGradebook {

    //-----------------------------------------------------------------------------------
    //Variables

    mapping (address => bool) public override tas;

    mapping (uint => uint) public override max_scores;

    mapping (uint => string) public override assignment_names;

    mapping (uint => mapping(string => uint)) public override scores;

    uint public override num_assignments;

    address public override instructor;

    //-----------------------------------------------------------------------------------
    
    constructor () {
        instructor = msg.sender;
    }

    //-----------------------------------------------------------------------------------
    //Functions

    function designateTA(address ta) public override {
        require(instructor == msg.sender, "Only instructor can make TA.");
        tas[ta] = true;
    }

    function addAssignment(string memory name, uint max_score) public override  returns (uint){
        require(instructor == msg.sender || tas[msg.sender], "Only instructor or TA can add assignment.");
        require(max_score > 0, "Max score must be greater than zero.");
        assignment_names[num_assignments] = name;
        max_scores[num_assignments] = max_score;
        emit assignmentCreationEvent(num_assignments);
        num_assignments++;
        return num_assignments - 1;
    }

    function addGrade(string memory student, uint assignment, uint score) public override {
        require(instructor == msg.sender || tas[msg.sender], "Only instructor or TA can add grade.");
        require(assignment >= 0 && assignment < num_assignments, "Assignment ID invalid.");
        require(score >= 0 && score <= max_scores[assignment], "Score exceeds max score.");

        scores[assignment][student] = score;
        emit gradeEntryEvent(assignment);
    }

    function getAverage(string memory student) public override view returns (uint) {
        uint points = 0;
        uint total_points = 0;
        for (uint i = 0; i < num_assignments; i++) {
            points += scores[i][student];
            total_points += max_scores[i];
        }
        return (10000*points)/total_points;
    }

    function requestTAAccess() public override {
        tas[msg.sender] = true;
    }

    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return interfaceId == type(IGradebook).interfaceId || interfaceId == 0x01ffc9a7;
    }
}