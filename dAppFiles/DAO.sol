// SPDX-License-Identifier: GPL-3.0-or-later
// mvy3ns Thomas Reiter

pragma solidity ^0.8.24;

import "./IERC165.sol";
import "./IDAO.sol";
import "./NFTManager.sol";
import "./Strings.sol";

contract DAO is IDAO {

    //-------------------------------------------------------------------------------------
    // Public Variables

    mapping (uint => Proposal) public override proposals;

    uint constant public override minProposalDebatePeriod = 600;

    address public override tokens;

    string constant public override purpose = "To lead the Fremen to the Green Paradise.";

    mapping (address => mapping (uint => bool)) public override votedYes;

    mapping (address => mapping (uint => bool)) public override votedNo;

    uint public override numberOfProposals;

    string constant public override howToJoin = "You must drink the Water of Life, then you will see how to join...";

    uint public override reservedEther;

    address public override curator;

    //-------------------------------------------------------------------------------------

    constructor() {
        NFTManager nftManager = new NFTManager("MookieNu", "MOOK");
        tokens = address(nftManager);
        curator = msg.sender;
        
        nftManager.mintWithURI(curator, "curatorbadge");
    }

    //-------------------------------------------------------------------------------------
    // Functions

    // This allows the function to receive ether without having a payable
    // function -- it doesn't have to have any code in its body, but it does
    // have to be present.
    receive() external payable {}

    // `msg.sender` creates a proposal to send `_amount` Wei to `_recipient`
    // with the transaction data `_transactionData`.  This can only be called
    // by a member of the DAO, and should revert otherwise.
    //
    // @param recipient Address of the recipient of the proposed transaction
    // @param amount Amount of wei to be sent with the proposed transaction
    // @param description String describing the proposal
    // @param debatingPeriod Time used for debating a proposal, at least
    //        `minProposalDebatePeriod()` seconds long.  Note that the 
    //        provided parameter can *equal* the `minProposalDebatePeriod()` 
    //        as well.
    // @return The proposal ID
    function newProposal(address recipient, uint amount, string memory description, 
                          uint debatingPeriod) public override payable returns (uint) {
        require(this.isMember(msg.sender), "Must be a member of the DAO.");
        require(debatingPeriod >= minProposalDebatePeriod, "Must be at least 600 seconds");
        require((address(this).balance - reservedEther) >= amount, "The DAO does not have enough funds.");

        Proposal memory newProp = Proposal({
            recipient: recipient,
            amount: amount,
            description: description,
            votingDeadline: block.timestamp + debatingPeriod,
            open: true,
            proposalPassed: false,
            yea: 0,
            nay: 0,
            creator: msg.sender
        });    

        proposals[numberOfProposals] = newProp;

        reservedEther += amount;

        emit NewProposal(numberOfProposals, recipient, amount, description);

        numberOfProposals++;

        return numberOfProposals - 1;
    }

    // Vote on proposal `_proposalID` with `_supportsProposal`.  This can only
    // be called by a member of the DAO, and should revert otherwise.
    //
    // @param proposalID The proposal ID
    // @param supportsProposal true/false as to whether in support of the
    //        proposal
    function vote(uint proposalID, bool supportsProposal) external override {
        require(this.isMember(msg.sender), "Must be a member of the DAO.");
        require(proposalID >= 0 && proposalID < numberOfProposals, "Invalid proposal ID.");
        require(block.timestamp < proposals[proposalID].votingDeadline, "Voting has ended for this proposal.");
        require(proposals[proposalID].open, "Proposal already closed.");
        require(!votedYes[msg.sender][proposalID] && !votedNo[msg.sender][proposalID], "You already voted for this.");

        if(supportsProposal){
            votedYes[msg.sender][proposalID] = true;
            proposals[proposalID].yea += 1;
        } else {
            votedNo[msg.sender][proposalID] = true;
            proposals[proposalID].nay += 1;
        }

        emit Voted(proposalID, supportsProposal, msg.sender);
    }

    // Checks whether proposal `_proposalID` with transaction data
    // `_transactionData` has been voted for or rejected, and transfers the
    // ETH in the case it has been voted for.  This can only be called by a
    // member of the DAO, and should revert otherwise.  It also reverts if
    // the proposal cannot be closed (time is not up, etc.).
    //
    // @param proposalID The proposal ID
    function closeProposal(uint proposalID) external override {
        require(this.isMember(msg.sender), "Must be a member of the DAO.");

        require(block.timestamp > proposals[proposalID].votingDeadline, "Voting has not ended for this proposal.");
        require(proposals[proposalID].open, "Proposal already closed.");

        if (proposals[proposalID].yea > proposals[proposalID].nay){
            (bool success, ) = payable(proposals[proposalID].recipient).call{value: proposals[proposalID].amount}("");
            require(success, "Failed to transfer ETH");

            proposals[proposalID].proposalPassed = true;
        }
        
        reservedEther -= proposals[proposalID].amount;

        proposals[proposalID].open = false;

        emit ProposalClosed(proposalID, proposals[proposalID].proposalPassed);
    }

    // Returns true if the passed address is a member of this DAO, false
    // otherwise.  This likely has to call the NFTManager, so it's not just a
    // public variable.  For this assignment, this should be callable by both
    // members and non-members.
    //
    // @param who An account address
    // @return A bool as to whether the passed address is a member of this DAO
    function isMember(address who) external override view returns (bool) {
        return NFTManager(tokens).balanceOf(who) > 0;
    }

    // Adds the passed member.  For this assignment, any current member of the
    // DAO can add members. Membership is indicated by an NFT token, so one
    // must be transferred to this member as part of this call.  This can only
    // be called by a member of the DAO, and should revert otherwise.
    // @param who The new member to add
    //
    // @param who An account address to have join the DAO
    function addMember(address who) external override {
        require(this.isMember(msg.sender), "Must be a member of DAO to add member");
        string memory uri = this.substring(Strings.toHexString(who),2,34);
        NFTManager(tokens).mintWithURI(who, uri);
    }

    // This is how one requests to join the DAO.  Presumably they called
    // howToJoin(), and fulfilled any requirement(s) therein.  In a real
    // application, this would put them into a list for the owner(s) to
    // approve or deny.  For our uses, this will automatically allow the
    // caller (`msg.sender`) to be a member of the DAO.  This functionality
    // is for grading purposes.  This function should revert if the caller is
    // already a member.
    function requestMembership() public override {
        require(!this.isMember(msg.sender), "You are already a member! (bozo)");
        string memory uri = this.substring(Strings.toHexString(msg.sender),2,34);
        NFTManager(tokens).mintWithURI(msg.sender, uri);
    }

    // also supportsInterface() from IERC165; it should support two
    // interfaces (IERC165 and IDAO)
    function supportsInterface(bytes4 interfaceId) external override pure returns(bool){
        return interfaceId == type(IERC165).interfaceId || interfaceId == type(IDAO).interfaceId;
    }

    //--------------------------------------------------------------------------------------------
    // Helper Functions

    function substring(string memory str, uint startIndex, uint endIndex) public pure returns (string memory) {
        bytes memory strBytes = bytes(str);
        bytes memory result = new bytes(endIndex-startIndex);
        for(uint i = startIndex; i < endIndex; i++)
            result[i-startIndex] = strBytes[i];
        return string(result);
    }

}