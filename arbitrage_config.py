# This is the config file for the Arbitrage homework
# https://aaronbloomfield.github.io/ccc/hws/arbitrage/

import hexbytes

# The configuration options to connect to the blockchain and the DEXes; this is the spring 2024 version
config = {
    # you will have to change these values for it to work
    'account_address': '0x1f972f3625BDDb3F582a31fC6aB3533FdA6bf720',
    'account_private_key': hexbytes.HexBytes('4da48dc9f70ba96f452a6daffea419cc6a0248d5878aa28ad5ff43262212f38a'),
    'connection_uri': 'wss://andromeda.cs.virginia.edu/geth',
    'connection_is_ipc': False, # set to false if it's a ws:// or wss:// connection
    # once set, these should only be changed as necessary as you are testing your code
    'price_eth': 100.00,
    'price_tc': 10.0,
    'max_eth_to_trade': 10.0,
    'max_tc_to_trade': 100.0,
    'gas_price': 10, # in gwei
    # once set, you should not have to change these
    'dex_addrs': [
        '0x3270c4e2712a094773f360223268737b4f76d4db', # D4 DEX
        '0x08942ee9050f1bfd446298e0a36c45b61df951a3', # D6 DEX
        '0xb48cff2e10bab7a40eed8e795b47abe4031c2057', # D8 DEX
        '0xd53a424d33d254d08dc88d86b7636423941805d7', # D10 DEX
        '0x897d3fb345ce0a3c54cbba807e7188a8ea1452bd', # D12 DEX
        '0x6b2c410bd8c822e5e8ccebd27bf3af4c7cd8409c', # D20 DEX
    ],
    'tokencc_addr': '0x60D154B23cD98A7Ac656417927876dd4FC9AbE52',
    'chainId': 67834505,
}


# This will print the output into the format required by the homework.  It
# should not be changed.  Whichever of ethDelta or tccDelta is sent should be
# negative, and whichever one is received should be positive.  Both of those
# values should be divided by 10**decimals (for tccDelta) or 10**18
# (for ethDelta). fees and holdings should be in USD as a float.
def output(ethDelta, tccDelta, fees, holdings_after):
    if ethDelta == 0 and tccDelta == 0:
        print("No profitable arbitrage trades available")
        return
    assert ethDelta * tccDelta < 0, f"Exactly one of ethDelta {ethDelta} and tccDelta {tccDelta} should be negative, the other positive"
    if ethDelta < 0:
        print("Exchanged %.4f ETH for %.4f TC; fees: %.2f USD; prices: ETH %.2f USD, TC: %.2f USD; holdings: %.2f USD" %
              (abs(ethDelta), abs(tccDelta), fees, config['price_eth'], config['price_tc'], holdings_after))
    else:
        print("Exchanged %.4f TC for %.4f ETH; fees: %.2f USD; prices: ETH %.2f USD, TC: %.2f USD; holdings: %.2f USD" %
              (abs(tccDelta), abs(ethDelta), fees, config['price_eth'], config['price_tc'], holdings_after))


# This is the ABI for IDEX.sol (this includes the functions inherited from IERC165 and IERC20Receiver)
idex_abi = '[{"anonymous":false,"inputs":[],"name":"liquidityChangeEvent","type":"event"},{"inputs":[],"name":"addLiquidity","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_tokenAmount","type":"uint256"},{"internalType":"uint256","name":"_feeNumerator","type":"uint256"},{"internalType":"uint256","name":"_feeDenominator","type":"uint256"},{"internalType":"address","name":"_erc20token","type":"address"},{"internalType":"address","name":"_etherPricer","type":"address"}],"name":"createPool","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"erc20Address","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"who","type":"address"}],"name":"etherLiquidityForAddress","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"etherPricer","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feeDenominator","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feeNumerator","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feesEther","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"feesToken","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getDEXinfo","outputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"string","name":"","type":"string"},{"internalType":"string","name":"","type":"string"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"},{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getEtherPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getPoolLiquidityInUSDCents","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getTokenPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"k","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"address","name":"erc20","type":"address"}],"name":"onERC20Received","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amountEther","type":"uint256"}],"name":"removeLiquidity","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"reset","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"p","type":"address"}],"name":"setEtherPricer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"who","type":"address"}],"name":"tokenLiquidityForAddress","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"x","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"y","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"stateMutability":"payable","type":"receive"}]';

# This is the ABI for ITokenCC.sol (this includes the functions inherited from IERC20Metadata, IERC20, and IERC165)
itokencc_abi = '[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"spender","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":false,"internalType":"uint256","name":"value","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"requestFunds","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"transferFrom","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]';


# This function will attempt to determine a return value or why a transaction
# reverted.  It will return one of three values:
# - None when it encounters an error (not when it encounters a revert)
# - (True,<ret>) if the TXN returned a value; the value is <ret>
# - (False,<str>) if the TXN reverted; the revert reason is <str>
def getTXNResult(w3,txhash):
    try:
        tx = w3.eth.get_transaction(txhash)
    except Exception as e:
        print("Error getting transaction:",e)
        return None
    replay_tx = {
        'to': tx['to'],
        'from': tx['from'],
        'value': tx['value'],
        'data': tx['input'],
        'gas': tx['gas'],
    }
    # replay the transaction locally:
    try:
        ret = w3.eth.call(replay_tx, tx.blockNumber - 1)
        return (True,ret)
    except Exception as e: 
        # it might be one of those cases where it worked correctly the first time, but bombed on the replay
        txrcpt = w3.eth.get_transaction_receipt(txhash)
        if txrcpt['status'] == 1:
            return (True,None)
        else:
            return (False,str(e))
