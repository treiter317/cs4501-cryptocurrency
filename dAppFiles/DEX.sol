// SPDX-License-Identifier: GPL-3.0-or-later
// mvy3ns Thomas Reiter

pragma solidity ^0.8.24;

import "./IDEX.sol";
import "./IERC165.sol";
import "./IEtherPriceOracle.sol";
import "./IERC20Receiver.sol";
import "./ERC20.sol";
import "./IERC20.sol";

contract DEX is IDEX {

    //-----------------------------------------------------------------------
    // Public Variables

    uint public override decimals;

    uint public override k;

    uint public override x;

    uint public override y;

    uint public override feeNumerator;

    uint public override feeDenominator;

    uint public override feesEther;

    uint public override feesToken;

    address public override etherPricer;

    address public override ERC20Address;

    mapping (address => uint) public override etherLiquidityForAddress;

    mapping (address => uint) public override tokenLiquidityForAddress;

    //additional variables not in interface

    bool internal poolCreated;

    address internal deployer;

    bool internal adjustingLiquidity;

    //---------------------------------------------------------------------------

    constructor() {
        poolCreated = false;
        adjustingLiquidity = false;
        deployer = msg.sender;
        k = 0;
        x = 0;
        y = 0;
    }

    //---------------------------------------------------------------------------
    // Functions

    function symbol() external view returns (string memory) {
        return ERC20(ERC20Address).symbol();
    }

    function getEtherPrice() external view returns (uint) {
        return IEtherPriceOracle(etherPricer).price();
    }

    //TODO: make sure exchange is fine with decimals?
    function getTokenPrice() external view returns (uint) {
        uint ethAmount = x / (10**18);
        uint TCCAmount = y;
        uint ethPrice = this.getEtherPrice();

        return ethPrice * (TCCAmount/ethAmount) / (10**(decimals+2));
    }

    function getPoolLiquidityInUSDCents() external view returns (uint) {
        return (this.getEtherPrice() * x * 2) / (10**18);
    }

    function setEtherPricer(address p) external {
        etherPricer = p;
    }

    // Functions for efficiency

    // this function is just to lower the number of calls to the contract from
    // the dex.php web page; it just returns the information in many of the
    // above calls as a single call.  The information it returns is a tuple
    // and is, in order:
    //
    // 0: the address of *this* DEX contract (address)
    // 1: token cryptocurrency abbreviation (string memory)
    // 2: token cryptocurrency name (string memory)
    // 3: ERC-20 token cryptocurrency address (address)
    // 4: k (uint)
    // 5: ether liquidity (uint)
    // 6: token liquidity (uint)
    // 7: fee numerator (uint)
    // 8: fee denominator (uint)
    // 9: token decimals (uint)
    // 10: fees collected in ether (uint)
    // 11: fees collected in the token CC (uint)
    function getDEXinfo() external view returns (address, string memory, string memory, 
                                                 address, uint, uint, uint, uint, uint, uint, uint, uint) {
        require(poolCreated, "Pool has not been created.");
        
        return (address(this), this.symbol(), ERC20(ERC20Address).name(), ERC20Address, k, 
                x, y, feeNumerator, feeDenominator, decimals, feesEther, feesToken);
    }

    function reset() external pure {
        revert();
    }

    function createPool(uint _tokenAmount, uint _feeNumerator, uint _feeDenominator, 
                        address _erc20token, address _etherPricer) external payable {

        require(!poolCreated, "Pool has already been created.");
        require(msg.sender == deployer, "Only deployer can create a pool.");
        require(_tokenAmount > 0, "Token amount must be greater than 0");
        require(msg.value > 0, "Ether amount must be greater than 0");
        require(_feeDenominator > 0, "Denominator can't be 0.");

        ERC20Address = _erc20token;

        require(IERC20(ERC20Address).balanceOf(msg.sender) >= _tokenAmount, "Insufficient token balance.");

        IERC20(ERC20Address).approve(address(this), _tokenAmount);
        IERC20(ERC20Address).transferFrom(msg.sender, address(this), _tokenAmount);
    
        decimals = ERC20(ERC20Address).decimals();
        etherPricer = _etherPricer;
        feeNumerator = _feeNumerator;
        feeDenominator = _feeDenominator;
        x = msg.value;
        y = _tokenAmount;
        k = x*y;

        poolCreated = true;

        emit liquidityChangeEvent();
    }

    // Anybody can add liquidity to the pool.  The amount of ETH is paid along
    // with the function call.  The caller will have to approve the
    // appropriate amount of token cryptocurrency, via the ERC-20 contract,
    // for this call to complete successfully.  Note that this function does
    // NOT remove any fees.
    function addLiquidity() external payable {
        require(poolCreated, "Pool has not been created.");

        adjustingLiquidity = true;

        uint ethAdded = msg.value / (10**18);
        uint exchangeRate = y/(x / (10**18));
        uint TCCToAdd = ethAdded * exchangeRate;

        require(IERC20(ERC20Address).balanceOf(msg.sender) >= TCCToAdd, "Insufficient token balance.");

        IERC20(ERC20Address).transferFrom(msg.sender, address(this), TCCToAdd);

        x += msg.value;
        y += TCCToAdd;
        k = x*y;

        etherLiquidityForAddress[msg.sender] = msg.value;
        tokenLiquidityForAddress[msg.sender] = TCCToAdd;

        adjustingLiquidity = false;

        emit liquidityChangeEvent();
    }

    // Remove liquidity -- both ether and token -- from the pool.  The ETH is
    // paid to the caller, and the token cryptocurrency is transferred back
    // as well.  If the parameter amount is more than the amount the address
    // has stored in the pool, this should revert.  See the homework
    // description for how fees are managed and paid out, but note that this
    // function does NOT remove any fees.  For this assignment, they cannot
    // take out more ether than they put in, and the amount of TCC that comes
    // with that cannot be more than they put in.  If the exchange rates are
    // much different, this could cause issues, but we are not going to deal
    // with those issues in this assignment, so you can ignore factoring in
    // different exchange rates.
    function removeLiquidity(uint amountWei) external {
        require(amountWei <= address(this).balance, "Can't take out more than amount in pool.");
        require (amountWei <= etherLiquidityForAddress[msg.sender], "Can't take out more than you put in.");
        require(poolCreated, "Pool has not been created.");

        adjustingLiquidity = true;

        uint ethToPay = amountWei/(10**18);
        uint exchangeRate = y/(x / (10**18));
        uint TCCToPay = (ethToPay * exchangeRate);

        require (TCCToPay <= tokenLiquidityForAddress[msg.sender], "Can't take out more than you put in.");

        IERC20(ERC20Address).approve(msg.sender, TCCToPay);
        IERC20(ERC20Address).transferFrom(address(this), msg.sender, TCCToPay);

        (bool success, ) = payable(msg.sender).call{value: amountWei}("");
        require (success, "Unsuccessful payment of eth.");

        x -= amountWei;
        y -= TCCToPay;
        k = x*y;

        adjustingLiquidity = false;

        emit liquidityChangeEvent();
    }

    // Swaps ether for token.  The amount of ETH is passed in as payment along
    // with this call.  Note that the receive() function is of a special form, 
    // and does not have the `function` keyword.
    receive() external payable {
        require(poolCreated, "Pool has not been created.");

        x += msg.value;
        uint newY = k/x;
        uint TCCToPay = y - newY;
        uint TCCFees = (TCCToPay * feeNumerator) / feeDenominator;
        TCCToPay -= TCCFees;

        IERC20(ERC20Address).approve(msg.sender, TCCToPay);
        IERC20(ERC20Address).transferFrom(address(this), msg.sender, TCCToPay);

        feesToken += TCCFees;
        y = newY;

        emit liquidityChangeEvent();
    }

    // Swap token for ether.  The ERC-20 smart contract for the token
    // cryptocurrency must be approved to transfer that much into the DEX,
    // and the appropriate amount of ETH is paid back to the caller.
    // This function is defined in the IERC20Receiver.sol file
    //
    function onERC20Received(address from, uint amount, address erc20) external returns (bool) {
        require(erc20 == ERC20Address, "Your TCC is worth nothing compared to $MOOK...");
        require(poolCreated, "Pool has not been created.");

        bool success = true;

        if (!adjustingLiquidity) {
            y += amount;
            uint newX = k/y;
            uint weiToPay = x - newX;
            uint ethFees = (weiToPay * feeNumerator) / feeDenominator;
            weiToPay -= ethFees;

            (success, ) = payable(from).call{value: weiToPay}("");
            require (success, "Ether transfer was unsuccessful.");

            x -= weiToPay;
            feesEther += ethFees;
        }

        emit liquidityChangeEvent();

        return success;
    }

    function supportsInterface(bytes4 interfaceId) external pure returns(bool){
        return interfaceId == type(IERC165).interfaceId || 
        interfaceId == type(IDEX).interfaceId || 
        interfaceId == type(IERC165).interfaceId || 
        interfaceId == type(IERC20Receiver).interfaceId;
    }
}