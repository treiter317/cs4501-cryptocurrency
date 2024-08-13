// SPDX-License-Identifier: GPL-3.0-or-later
// Thomas Reiter mvy3ns

pragma solidity ^0.8.24;

import "./INFTManager.sol";
import "./ERC721.sol";
import "./Strings.sol";

contract NFTManager is INFTManager, ERC721 {

    uint public override count;

    mapping (uint => string) public tokens;

    constructor() ERC721("MookieNu", "MOOK") {}

    function mintWithURI(address _to, string memory _uri) public override returns (uint) {
        bool uriExists;
        for (uint i = 0; i < count; i++) 
        {
            if (Strings.equal(_uri, tokens[i])) {
                uriExists = true;
                break;
            }
        }
        require(!uriExists, "URI already exists.");

        ERC721._mint(_to, count);
        tokens[count] = _uri;
        count++;
        return count-1;
    }

    function mintWithURI(string memory _uri) public override returns (uint) {
        return mintWithURI(msg.sender, _uri);
    }

    function _baseURI() internal override view virtual returns (string memory) {
        return "https://andromeda.cs.virginia.edu/ccc/ipfs/files/";
    }

    function tokenURI(uint256 tokenId) public override(ERC721, IERC721Metadata) view virtual returns (string memory) {
        require(tokenId >= 0 && tokenId < count, "Invalid token ID.");

        return string.concat(_baseURI(), tokens[tokenId]);
    }

    function supportsInterface(bytes4 interfaceId) public override(ERC721, IERC165) pure returns(bool){
        return interfaceId == type(IERC165).interfaceId || 
        interfaceId == type(IERC721).interfaceId || 
        interfaceId == type(IERC721Metadata).interfaceId || 
        interfaceId == type(INFTManager).interfaceId;
    }
}