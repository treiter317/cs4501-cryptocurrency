// SPDX-License-Identifier: GPL-3.0-or-later
// Thomas Reiter mvy3ns

pragma solidity ^0.8.24;

import "./IAuctioneer.sol";
import "./NFTManager.sol";
import "./ERC721.sol";

contract Auctioneer is IAuctioneer {

    // Public Variables
    //-----------------------------------------------------------
    address public override nftmanager;

    uint public override numAuctions;

    uint public override totalFees;

    uint public override uncollectedFees;

    mapping (uint => Auction) public override auctions;

    address public override deployer;

    //-----------------------------------------------------------

    constructor() {
        NFTManager nftm = new NFTManager();
        nftmanager = address(nftm);
        deployer = msg.sender;
    }

    // Functions
    //-----------------------------------------------------------

    function collectFees() public override {
        (bool success, ) = payable(deployer).call{value: uncollectedFees}("");
        require(success, "Failed to transfer ETH");
        uncollectedFees = 0;
    }

    function startAuction(uint m, uint h, uint d, string memory data, uint reserve, uint nftid) public override returns (uint) {
        //sanity checks
        require(m > 0 || h > 0 || d > 0, "Must enter non zero amount of time.");
        require(bytes(data).length > 0, "Data can't be an empty string.");

        bool nftInAuction = false;
        for (uint i = 0; i < numAuctions; i++) {
            if(auctions[i].nftid == nftid && auctions[i].active) {
                nftInAuction = true;
                break;
            }
        }
        require(!nftInAuction, "NFT already in running auction.");
        require(msg.sender == NFTManager(nftmanager).ownerOf(nftid), "Only owner of NFT can start auction.");

        //transfer nft to the auctioneer contract
        NFTManager(nftmanager).transferFrom(msg.sender, address(this), nftid);

        //create the new auction as a struct
        Auction memory newAuction = Auction({
            id: numAuctions,
            num_bids: 0,
            data: data,
            highestBid: reserve,
            winner: address(0),
            initiator: msg.sender,
            nftid: nftid,
            endTime: block.timestamp + (60*m) + (3600*h) + (86400*d),
            active: true
        });
        auctions[numAuctions] = newAuction;

        emit auctionStartEvent(numAuctions);
        numAuctions++;
        return numAuctions-1;
    }

    function closeAuction(uint id) public override {
        //sanity checks
        require(id >= 0 && id < numAuctions, "Invalid auction id.");
        require(auctions[id].active, "Auction already closed.");
        require(block.timestamp > auctions[id].endTime, "Auction time must be expired to close.");

        //transfer winning bid eth to the initiator (include fees if there was successful bid)
        if (auctions[id].num_bids > 0) {
            uint bidFee = (auctions[id].highestBid / 100);
            totalFees += bidFee;
            uncollectedFees += bidFee;

            (bool success, ) = payable(auctions[id].initiator).call{value: (auctions[id].highestBid - bidFee)}("");
            require(success, "Failed to transfer ETH");

            //transfer nft to the winning bidder from the auction contract
            NFTManager(nftmanager).transferFrom(address(this), auctions[id].winner, auctions[id].nftid);
        }
        // no bids so return NFT to initiator
        else {
            NFTManager(nftmanager).transferFrom(address(this), auctions[id].initiator, auctions[id].nftid);
        }

        auctions[id].active = false;       

        emit auctionCloseEvent(id);
    }

    function placeBid(uint id) public payable override {
        //sanity checks
        require(id >= 0 && id < numAuctions, "Invalid auction id.");
        require(auctions[id].active, "Auction is inactive.");
        require(block.timestamp < auctions[id].endTime, "Auction bid period has ended.");

        // bid can be equal to reserve (which is initial highest bid) but later bids must be greater
        if (auctions[id].num_bids == 0){
            require(msg.value > 0, "Must make a non-zero bid.");
            require(msg.value >= auctions[id].highestBid, "Must make a bid at least as much as reserve.");
        } else {
            require(msg.value > auctions[id].highestBid, "Must make a higher bid.");
        }

        //refund previous highest bidder
        if(auctions[id].num_bids > 0) {
            (bool success, ) = payable(auctions[id].winner).call{value: auctions[id].highestBid}("");
            require(success, "Failed to transfer ETH");
        }

        //update auction struct
        auctions[id].highestBid = msg.value;
        auctions[id].winner = msg.sender;
        auctions[id].num_bids++;

        emit higherBidEvent(id);
    }

    function auctionTimeLeft(uint id) public view override returns (uint) {
        require(auctions[id].endTime > block.timestamp, "Auction time has ended!");
        
        return auctions[id].endTime - block.timestamp;
    }

    function supportsInterface(bytes4 interfaceId) public override pure returns(bool){
        return interfaceId == type(IERC165).interfaceId || interfaceId == type(IAuctioneer).interfaceId;
    }
}