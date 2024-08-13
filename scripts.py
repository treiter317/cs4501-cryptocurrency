#!/usr/bin/python3

# This is the homework submission file for the BTC Scripting homework, which
# can be found at http://aaronbloomfield.github.io/ccc/hws/btcscript.  That
# page describes how to fill in this program.

from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret
from bitcoin import SelectParams
from bitcoin.core import CMutableTransaction
from bitcoin.core.script import *
from bitcoin.core import x


#------------------------------------------------------------
# Do not touch: change nothing in this section!

# ensure we are using the bitcoin testnet and not the real bitcoin network
SelectParams('testnet')

# The address that we will pay our tBTC to -- do not change this!
tbtc_return_address = CBitcoinAddress('mohjSavDdQYHRYXcS3uS6ttaHP8amyvX78') # https://testnet-faucet.com/btc-testnet/

# The address that we will pay our BCY to -- do not change this!
bcy_dest_address = CBitcoinAddress('mgBT4ViPjTTcbnLn9SFKBRfGtBGsmaqsZz')

# Yes, we want to broadcast transactions
broadcast_transactions = True

# Ensure we don't call this directly
if __name__ == '__main__':
    print("This script is not meant to be called directly -- call bitcoinctl.py instead")
    exit()


#------------------------------------------------------------
# Setup: your information

# Your UVA userid
userid = 'mvy3ns'

# Enter the BTC private key and invoice address from the setup 'Testnet Setup'
# section of the assignment.  
my_private_key_str = "cQZNUYTyZa7spXQtueRj7AEtedcpMrGX6pVURnTHkeSYGZiDmJTE"
my_invoice_address_str = "mmcWW6bU8Z41d4KqvbQxYXdnxoJ6HbTpbo"

# Enter the transaction ids (TXID) from the funding part of the 'Testnet
# Setup' section of the assignment.  Each of these was provided from a faucet
# call.  And obviously replace the empty string in the list with the first
# one you botain..
txid_funding_list = ["b8ae4d5664104437a9bc6d2384c9f6046c862da7f1c31543e06e1da04339d828", "286ada14e48d31287a1d9b70c71c1b457e58fe450f15993ace7f4c31ec662cb0", "b8d13b0f33b1f882150f4bd43204f9fb61b257384b3a98c7ae5a07191a4955e8"]

# These conversions are so that you can use them more easily in the functions
# below -- don't change these two lines.
if my_private_key_str != "":
    my_private_key = CBitcoinSecret(my_private_key_str)
    my_public_key = my_private_key.pub


#------------------------------------------------------------
# Utility function(s)

# This function will create a signature of a given transaction.  The
# transaction itself is passed in via the first three parameters, and the key
# to sign it with is the last parameter.  The parameters are:
# - txin: the transaction input of the transaction being signed; type: CMutableTxIn
# - txout: the transaction output of the transaction being signed; type: CMutableTxOut
# - txin_scriptPubKey: the pubKey script of the transaction being signed; type: list
# - private_key: the private key to sign the transaction; type: CBitcoinSecret
def create_CHECKSIG_signature(txin, txout, txin_scriptPubKey, private_key):
    tx = CMutableTransaction([txin], [txout])
    sighash = SignatureHash(CScript(txin_scriptPubKey), tx, 0, SIGHASH_ALL)
    return private_key.sign(sighash) + bytes([SIGHASH_ALL])


#------------------------------------------------------------
# Testnet Setup: splitting coins

# The transaction ID that is to be split -- the assumption is that it is the
# transaction hash, above, that funded your account with tBTC.  You may have
# to split multiple UTXOs, so if you are splitting a different faucet
# transaction, then change this appropriately. It must have been paid to the
# address that corresponds to the private key above
txid_split = txid_funding_list[2]

# After all the splits, you should have around 10 (or more) UTXOs, all for the
# amount specified in this variable. That amount should not be less than
# 0.0001 BTC, and can be greater.  It will make your life easier if each
# amount is a negative power of 10, but that's not required.
split_amount_to_split = 0.0007

# How much BTC is in that UTXO; look this up on https://live.blockcypher.com
# to get the correct amount.
split_amount_after_split = 0.0001

# How many UTXO indices to split it into -- you should not have to change
# this!  Note that it will actually split into one less, and use the last one
# as the transaction fee.
split_into_n = int(split_amount_to_split/split_amount_after_split)

# The transaction IDs obtained after successfully splitting the tBTC.
txid_split_list = ["a5fc3c97d1addec09919a54286a7f9a57b66ec25d41249549491505643b369b9", "8349f8fa92198976a59d347b6ef71927dcdea8fe1bc4bebbcb18a972dfb3b313", "58e4cfbe92f38f2582dc133ae0f561c542eebf23c3169c2e2e91a3eb7f69ef97"]

#------------------------------------------------------------
# Global settings: some of these will need to be changed for EACH RUN

# The transaction ID that is being redeemed for the various parts herein --
# this should be the result of the split transaction, above; thus, the
# default is probably sufficient.
txid_utxo = txid_split_list[2]

# This is likely not needed.  The bitcoinctl.py will take a second
# command-line parmaeter, which will override this value.  You should use the
# second command-line parameter rather than this variable. The index of the
# UTXO that is being spent -- note that these indices are indexed from 0.
# Note that you will have to change this for EACH run, as once a UTXO index
# is spent, it can't be spent again.  If there is only one index, then this
# should be set to 0.
utxo_index = -1

# How much tBTC to send -- this should be LESS THAN the amount in that
# particular UTXO index -- if it's not less than the amount in the UTXO, then
# there is no miner fee, and it will not be mined into a block.  Setting it
# to 90% of the value of the UTXO index is reasonable.  Note that the amount
# in a UTXO index is split_amount_to_split / split_into_n.
send_amount = split_amount_after_split * 0.9


#------------------------------------------------------------
# Part 1: P2PKH transaction

# This defines the pubkey script (aka output script) for the transaction you
# are creating.  This should be a standard P2PKH script.  The parameter is:
# - address: the address this transaction is being paid to; type:
#   P2PKHBitcoinAddress
def P2PKH_scriptPubKey(address):
    return [
            OP_DUP, 
            OP_HASH160, 
            address, 
            OP_EQUALVERIFY, 
            OP_CHECKSIG
            ]

# This function provides the sigscript (aka input script) for the transaction
# that is being redeemed.  This is for a standard P2PKH script.  The
# parameters are:
# - txin: the transaction input of the UTXO being redeemed; type:
#   CMutableTxIn
# - txout: the transaction output of the UTXO being redeemed; type:
#   CMutableTxOut
# - txin_scriptPubKey: the pubKey script (aka output script) of the UTXO being
#   redeemed; type: list
# - private_key: the private key of the redeemer of the UTXO; type:
#   CBitcoinSecret
def P2PKH_scriptSig(txin, txout, txin_scriptPubKey, private_key):
    signature = create_CHECKSIG_signature(txin, txout, txin_scriptPubKey, private_key) # see the comments above for how to use create_CHECKSIG_signature()
    return [
            signature, 
            private_key.pub
            ]

# The transaction hash received after the successful execution of this part
txid_p2pkh = "cb7eb85a219e1074cdfbd4ea9092040b6f56cf8c96299badc0656d2b68987147"

#------------------------------------------------------------
# Part 2: puzzle transaction

# These two values are constants that you should choose -- they should be four
# digits long.  They need to allow for only integer solutions to the linear
# equations specified in the assignment.
puzzle_txn_p = 4944 #0x1350
puzzle_txn_q = 3528 #0xDC8

# These are the solutions to the linear equations specified in the homework
# assignment.  You can use an online linear equation solver to find the
# solutions.
puzzle_txn_x = 1416 #0x588
puzzle_txn_y = 2112 #0x840

# This function provides the pubKey script (aka output script) that requires a
# solution to the above equations to redeem this UTXO.
def puzzle_scriptPubKey():
    return [ 
             OP_OVER,
             OP_ADD,
             OP_DUP,
             puzzle_txn_q,
             OP_EQUALVERIFY,
             OP_ADD,
             puzzle_txn_p,
             OP_EQUAL,
           ]

# This function provides the sigscript (aka input script) for the transaction
# that you are redeeming.  It should only provide the two values x and y, but
# in the order of your choice.
def puzzle_scriptSig():
    return [ 
             puzzle_txn_x,
             puzzle_txn_y
           ]

# The transaction hash received after successfully submitting the first
# transaction above (part 2a)
txid_puzzle_txn1 = "6672ac1383782d745a9338f92f87bc40dee526b24dbba0e26827d4c13518752c"

# The transaction hash received after successfully submitting the second
# transaction above (part 2b)
txid_puzzle_txn2 = "fb81a42eb5debba7c90f86ae09959eb3b61a7506a30eb21c544c627ad39f3774"


#------------------------------------------------------------
# Part 3: Multi-signature transaction

# These are the public and private keys that need to be created for alice,
# bob, and charlie
alice_private_key_str = "cSCGoi3wtSavvcPUqjvJKopCZoKJmfz9KduA4i8qqUrTdVobypDT"
alice_invoice_address_str = "n1Xb4WQvKGFo283a5sLWNxKiTRRg3i1oY1"
bob_private_key_str = "cNY2eTFEtUeuuSArLWA8c33amTmejaar5o8g8fZfjKd1T3kH3v6t"
bob_invoice_address_str = "msSitU3jmdHMERUtZYh3tgYy6wTYx7xz46"
charlie_private_key_str = "cVLUUqHt6dmHMYjoxrW1V9vo7TfgsPHNFzerdRJGwZyDFaa7BBA3"
charlie_invoice_address_str = "mxCLayLRBc1ZyD6pREB9wstbWuqiZuB2Wi"

# These three lines convert the above strings into the type that is usable in
# a script -- you should NOT modify these lines.
if alice_private_key_str != "":
    alice_private_key = CBitcoinSecret(alice_private_key_str)
if bob_private_key_str != "":
    bob_private_key = CBitcoinSecret(bob_private_key_str)
if charlie_private_key_str != "":
    charlie_private_key = CBitcoinSecret(charlie_private_key_str)

# This function provides the pubKey script (aka output script) that will
# require multiple different keys to allow redeeming this UTXO.  It MUST use
# the OP_CHECKMULTISIGVERIFY opcode.  While there are no parameters to the
# function, you should use the keys above for alice, bob, and charlie, as
# well as your own key.
def multisig_scriptPubKey():
    return [
            OP_2,
            alice_private_key.pub,
            bob_private_key.pub,
            charlie_private_key.pub,
            OP_3,
            OP_CHECKMULTISIGVERIFY,
            my_private_key.pub,
            OP_CHECKSIG
           ]

# This function provides the sigScript (aka input script) that can redeem the
# above transaction.  The parameters are the same as for P2PKH_scriptSig
# (), above.  You also will need to use the keys for alice, bob, and charlie,
# as well as your own key.  The private key parameter used is the global
# my_private_key.
def multisig_scriptSig(txin, txout, txin_scriptPubKey):
    bank_sig = create_CHECKSIG_signature(txin, txout, txin_scriptPubKey, my_private_key)
    alice_sig = create_CHECKSIG_signature(txin, txout, txin_scriptPubKey, alice_private_key)
    bob_sig = create_CHECKSIG_signature(txin, txout, txin_scriptPubKey, bob_private_key)
    charlie_sig = create_CHECKSIG_signature(txin, txout, txin_scriptPubKey, charlie_private_key)
    return [
            bank_sig,
            OP_0,
            alice_sig,
            # bob_sig, treating bob as the one who doesn't sign
            charlie_sig,
           ]

# The transaction hash received after successfully submitting the first
# transaction above (part 3a)
txid_multisig_txn1 = "0148ad54f684831e1439752e4e413ec06598a88a34dc57435f0f58805974fc47"

# The transaction hash received after successfully submitting the second
# transaction above (part 3b)
txid_multisig_txn2 = "cf190e080f2aade110ece9d550674d5dbe68372c9ec918fc623a4bc96ec09bcd"
# da8c52bfc4deeb8e8437669b597598a25a06289d8cdaa1cde0eeeb3b9a0a31b5

#------------------------------------------------------------
# Part 4: cross-chain transaction

# This is the API token obtained after creating an account on
# https://accounts.blockcypher.com/.  This is optional!  But you may want to
# keep it here so that everything is all in once place.
blockcypher_api_token = "e5526d93e0f243d0a5b12afa8fef3d10"

# These are the private keys and invoice addresses obtained on the BCY test
# network.
my_private_key_bcy_str = "240aab8fe0383fdd077b4e19577590149aac79ee37c072871e9c64faa823751e"
my_invoice_address_bcy_str = "CFC4LgfMR82GonmZf3WCbD4NWhwovcqGTC"
bob_private_key_bcy_str = "64ecd323d238a29baccc816897da7b6b3bf1bf8ddea460928bf550d205e50d57"
bob_invoice_address_bcy_str = "BxwE6SMt8NAHZyg1xMkLYabfN7GbMPdzWH"

# This is the transaction hash for the funding transaction for Bob's BCY
# network wallet.
txid_bob_bcy_funding = "b269d95a7faa41dd9c2de58461821ed408520f073a4fb2a4cdd71c67a7467e99"

# This is the transaction hash for the split transaction for the trasnaction
# above.
txid_bob_bcy_split = "2e07d39ce87e373281aac7f483604a5fd40584050df048207baad073b9ee5e49"

# This is the secret used in this atomic swap.  It needs to be between 1 million
# and 2 billion.
atomic_swap_secret = 483586204

# This function provides the pubKey script (aka output script) that will set
# up the atomic swap.  This function is run by both Alice (aka you) and Bob,
# but on different networks (tBTC for you/Alice, and BCY for Bob).  This is
# used to create TXNs 1 and 3, which are described at
# http://aaronbloomfield.github.io/ccc/slides/bitcoin.html#/xchainpt1.
def atomicswap_scriptPubKey(public_key_sender, public_key_recipient, hash_of_secret):
    return [ 
             OP_IF,
                OP_HASH160,
                hash_of_secret,
                OP_EQUALVERIFY,
                public_key_recipient,
                OP_CHECKSIG,
             OP_ELSE,
                OP_0,
                OP_0,
                OP_2SWAP,
                OP_2,
                public_key_sender,
                public_key_recipient, 
                OP_2,
                OP_CHECKMULTISIG,
             OP_ENDIF
           ]

# This is the ScriptSig that the receiver will use to redeem coins.  It's
# provided in full so that you can write the atomicswap_scriptPubKey()
# function, above.  This creates the "normal" redeeming script, shown in steps 5 and 6 at 
# http://aaronbloomfield.github.io/ccc/slides/bitcoin.html#/atomicsteps.
def atomcswap_scriptSig_redeem(sig_recipient, secret):
    return [
        sig_recipient, secret, OP_TRUE,
    ]

# This is the ScriptSig for sending coins back to the sender if unredeemed; it
# is provided in full so that you can write the atomicswap_scriptPubKey()
# function, above.  This is used to create TXNs 2 and 4, which are
# described at
# http://aaronbloomfield.github.io/ccc/slides/bitcoin.html#/xchainpt1.  In
# practice, this would be time-locked in the future -- it would include a
# timestamp and call OP_CHECKLOCKTIMEVERIFY.  Because the time can not be
# known when the assignment is written, and as it will vary for each student,
# that part is omitted.
def atomcswap_scriptSig_refund(sig_sender, sig_recipient):
    return [
        sig_recipient, sig_sender, OP_FALSE,
    ]

# The transaction hash received after successfully submitting part 4a
txid_atomicswap_alice_send_tbtc = "7077d8bfb7e6de950e2a41fdbb955445e3a4107550d681b4e4e709dcbe37b95e"

# The transaction hash received after successfully submitting part 4b
txid_atomicswap_bob_send_bcy = "37d86d1334a17feb0d2550f05f6b28c74604181e868b9d65d2c5a6a0e00f0768"

# The transaction hash received after successfully submitting part 4c
txid_atomicswap_alice_redeem_bcy = "80b1f618b1d14bbc07eb2312afbbf2c2545187081bf405507f6dbb9f2a6aa3d8"

# The transaction hash received after successfully submitting part 4d
txid_atomicswap_bob_redeem_tbtc = "c012f02a4ebf74346ce1fa9506e1428d7fb5abf26ce4945d9af0ba76290fd53b"


#------------------------------------------------------------
# part 5: return everything to the faucet

# nothing to fill in here, as we are going to look at the balance of
# `my_invoice_address_str` to verify that you've completed this part.
