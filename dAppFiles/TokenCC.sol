// SPDX-License-Identifier: MIT
// Thomas Reiter mvy3ns

pragma solidity ^0.8.24;

import "./ITokenCC.sol";
import "./ERC20.sol";
import "./IERC20Receiver.sol";

contract TokenCC is ITokenCC, ERC20 {
    constructor() ERC20("MookieNu", "MOOK") {
        _mint(msg.sender, 100000000 * 10**9);
    }

    function decimals() public pure override(ERC20, IERC20Metadata) returns (uint8) {
        return 9;
    }

    function requestFunds() public pure override {
        revert();
    }

    // This overrides the _update() function in ERC20.sol -- first we call the
    // overridden function, then we call afterTokenTransfer().  Note that this is
    // called on a mint, burn, or transfer.
    function _update(address from, address to, uint256 value) internal override virtual {
        ERC20._update(from,to,value);
        afterTokenTransfer(from,to,value);
    }

    // When a transfer occurs to a contract, this function will call
    // onERC20Received() on that contract.
    function afterTokenTransfer(address from, address to, uint256 amount) internal {
        if ( to.code.length > 0  && from != address(0) && to != address(0) ) {
            // token recipient is a contract, notify them
            try IERC20Receiver(to).onERC20Received(from, amount, address(this)) returns (bool success) {
                require(success,"ERC-20 receipt rejected by destination of transfer");
            } catch {
                // the notification failed (maybe they don't implement the `IERC20Receiver` interface?)
                // we choose to silently ignore this case
            }
        }
    }

    function supportsInterface(bytes4 interfaceId) external pure returns(bool){
        return interfaceId == type(IERC165).interfaceId || 
        interfaceId == type(IERC20).interfaceId || 
        interfaceId == type(IERC20Metadata).interfaceId || 
        interfaceId == type(ITokenCC).interfaceId;
    }
}