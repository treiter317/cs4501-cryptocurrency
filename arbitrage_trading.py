#mvy3ns Thomas Reiter
# CS 4501 HW 10: Arbitrage Trading

from web3 import Web3
from hexbytes import HexBytes
from web3.middleware import geth_poa_middleware
import arbitrage_config
import math

#Must handle web3 connection to blockchain at start
if arbitrage_config.config['connection_is_ipc']:
    w3 = Web3(Web3.IPCProvider(arbitrage_config.config['connection_uri']))
else:
    w3 = Web3(Web3.WebsocketProvider(arbitrage_config.config['connection_uri']))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# constants collected from config
dex_abi = arbitrage_config.idex_abi
tcc_abi = arbitrage_config.itokencc_abi

# initializing the tcc contract since all dexes use same tcc
tcc = w3.eth.contract(address=Web3.to_checksum_address(arbitrage_config.config['tokencc_addr']), abi=tcc_abi)

# more config constants
account = arbitrage_config.config['account_address']
price_eth = arbitrage_config.config['price_eth']
price_tcc = arbitrage_config.config['price_tc']
gas_price = arbitrage_config.config['gas_price']
max_eth_trade = arbitrage_config.config['max_eth_to_trade']
max_tcc_trade = arbitrage_config.config['max_tc_to_trade']
chainId = arbitrage_config.config['chainId']
private_key = arbitrage_config.config['account_private_key']

tcc_decimals = tcc.functions.decimals().call()

# this will store the contract objects for each active dex
dex_contracts = {}

# functions used to calculate trades. Most are helper functions and txns actually occur in makeTrade()
def findTCMaxMin(dex_id):
    x, y, k, f = getDEXValues(dex_id)
    delta = f * k * (price_eth / price_tcc)
    root1 = -y + math.sqrt(delta)
    root2 = -y - math.sqrt(delta)
    return root1, root2

def findETHMaxMin(dex_id):
    x, y, k, f = getDEXValues(dex_id)
    delta = f * k * (price_tcc / price_eth)
    root1 = -x + math.sqrt(delta)
    root2 = -x - math.sqrt(delta)
    return root1, root2

def calculateCurrentHoldings():
    q_eth = float(w3.from_wei(w3.eth.get_balance(account), 'ether')) # amount of ether account holds

    q_tcc = tcc.functions.balanceOf(account).call()
    q_tcc = float(q_tcc / (10 ** tcc_decimals)) # amount of tcc account holds without decimals

    return round((q_eth * price_eth) + (q_tcc * price_tcc), 2)

def calculateHoldingsAfter(currency, delta, dex_num, g):
    x, y, k, f = getDEXValues(dex_num)

    q_e = float(w3.from_wei(w3.eth.get_balance(account), 'ether'))
    q_t = float(tcc.functions.balanceOf(account).call() / (10 ** tcc_decimals))

    # formulas from the website
    if currency == "e":
        h = ((q_t + (f * y) - (f * (k / (x + delta)))) * price_tcc) + ((q_e - delta) * price_eth) - (g * price_eth)
    else:
        h =  ((q_e + (f * x) - (f * (k / (y + delta)))) * price_eth) + ((q_t - delta) * price_tcc) - (g * price_eth)

    return h

def getDEXValues(dex_id):
    dex_contract = dex_contracts[dex_id]
    x = dex_contract.functions.x().call()
    y = dex_contract.functions.y().call()
    k = dex_contract.functions.k().call()
    f = 1 - (float(dex_contract.functions.feeNumerator().call()) / float(dex_contract.functions.feeDenominator().call()))

    x = x / 10**18
    y = y / 10**tcc_decimals
    k = k / 10**(18+tcc_decimals)

    return x, y, k, f

def makeTrade():
    dex_addresses = arbitrage_config.config["dex_addrs"]

    # creates the contract object for the active dexes from the config file
    for i, dex in enumerate(dex_addresses):
        dex = Web3.to_checksum_address(dex)
        dex_contracts[i] = w3.eth.contract(address=dex, abi=dex_abi)

    # store balance for use below
    tcc_balance = float( tcc.functions.balanceOf(account).call() / (10**tcc_decimals) )
    eth_balance = float( w3.from_wei(w3.eth.get_balance(account), 'ether') )

    # approximated average of gas value
    g = (200000 * gas_price) / (10**9)

    # looks at each dex to find the optimal trades
    potential_trades = []
    potential_txns = []

    for i in range(len(dex_contracts)):
        delta_e = findETHMaxMin(i)
        delta_t = findTCMaxMin(i)

        # looks at the two roots found for each dex and currency
        for j in range(2):
            # only look at positive deltas
            if(delta_e[j] > 0):
                eth_trade_amount = delta_e[j]

                # cap the trade amount at the balance the user has
                if eth_trade_amount > eth_balance:
                    eth_trade_amount = eth_balance - g

                txn_e = {
                    'nonce': w3.eth.get_transaction_count(account),
                    'from': account,
                    'to': Web3.to_checksum_address(dex_addresses[i]),
                    'value': w3.to_wei(str(eth_trade_amount), 'ether'),
                    'gas': 3000000,
                    'gasPrice': w3.to_wei(str(gas_price), 'gwei'),
                    'chainId': chainId,
                }

                #calculate gas; value will be in gas units
                gas = w3.eth.estimate_gas(txn_e)
                g = (gas * gas_price) / (10**9) # gas spent in ether

                # calculate profitability!!
                profit = calculateHoldingsAfter("e", eth_trade_amount, i, g) - calculateCurrentHoldings()

                # save the trade for later 
                if profit > 0:
                    potential_trades.append([i, 'e', eth_trade_amount, profit])
                    potential_txns.append(txn_e)

            if (delta_t[j] > 0) & (tcc_balance > 0):
                tcc_trade_amount = delta_t[j]

                # cap trade amount by balance
                if tcc_trade_amount > tcc_balance:
                    tcc_trade_amount = tcc_balance

                # caps it at the tcc maximum and adds the decimals
                tcc_trade_amount = min(int(tcc_trade_amount * (10**tcc_decimals)), int(max_tcc_trade * (10**tcc_decimals)))

                txn_t = tcc.functions.transfer(Web3.to_checksum_address(dex_addresses[i]), tcc_trade_amount).build_transaction({
                    'nonce': w3.eth.get_transaction_count(account),
                    'from': account,
                    'gas': 3000000,
                    'gasPrice': w3.to_wei(str(gas_price), 'gwei'),
                    'chainId': chainId,
                })

                # convert tcc trade amount back to non decimal value
                tcc_trade_amount = tcc_trade_amount / (10**tcc_decimals)

                #calculate gas; value will be in gas units
                gas = w3.eth.estimate_gas(txn_t)
                g = (gas * gas_price) / (10**9) # gas spent in ether
                
                # calculate profitability!!
                profit = calculateHoldingsAfter("t", tcc_trade_amount, i, g) - calculateCurrentHoldings()

                if profit > 0:
                    potential_trades.append([i, 't', tcc_trade_amount, profit])
                    potential_txns.append(txn_t)


    # get the most profitable trade from the potential trades IF one exists
    if len(potential_trades) > 0:
        max_index, max_trade = max(enumerate(potential_trades), key=lambda x: x[1][3])
        best_txn = potential_txns[max_index]

        # cap the eth trade amount if greater than the maximum in config, already did this for TCC
        if (max_trade[1] == 'e') & (max_trade[2] > max_eth_trade):
            max_trade[2] = int(max_eth_trade)
            best_txn['value'] = w3.to_wei(str(max_eth_trade), 'ether')

        # get balances before txn
        before_eth_balance = eth_balance
        before_tcc_balance = tcc_balance

        # NOW create the transaction
        signed_txn = w3.eth.account.sign_transaction(best_txn, private_key=private_key)
        ret = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        result = arbitrage_config.getTXNResult(w3, ret)

        # get the info from the dex we are trading to
        x, y, k, f = getDEXValues(max_trade[0])

        # get new balances after txn
        if max_trade[1] == 'e':
            amount_transacted = max_trade[2]
            eth_balance_after = eth_balance - amount_transacted
            tcc_balance_after = tcc_balance + (f * y) - (f * k / (x + amount_transacted))
        else:
            amount_transacted = max_trade[2]
            eth_balance_after = eth_balance + (f * x) - (f * k / (y + amount_transacted))
            tcc_balance_after = tcc_balance - amount_transacted

        gas_fees = g * price_eth
        eth_delta = eth_balance_after - before_eth_balance
        tcc_delta = tcc_balance_after - before_tcc_balance
    else:
        # no trade available
        result = (True, True)
        gas_fees = 0
        eth_delta = 0
        tcc_delta = 0
    
    if result[0]:
        arbitrage_config.output(eth_delta, tcc_delta, gas_fees, calculateCurrentHoldings())
    else:
        print(result[1])


# execute the program!
makeTrade()