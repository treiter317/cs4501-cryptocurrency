import sys, binascii, hashlib, rsa, datetime, os

command = sys.argv[1]

# gets the hash of a file; from https://stackoverflow.com/a/44873382
def hashFile(filename):
    h = hashlib.sha256()
    with open(filename, 'rb', buffering=0) as f:
        for b in iter(lambda : f.read(128*1024), b''):
            h.update(b)
    return h.hexdigest()

# Load the wallet keys from a filename
def loadWallet(filename):
    with open(filename, mode='rb') as file:
        keydata = file.read()
    privkey = rsa.PrivateKey.load_pkcs1(keydata)
    pubkey = rsa.PublicKey.load_pkcs1(keydata)
    return pubkey, privkey

def getWalletTag(filename):
    with open(filename, 'r') as file:
        next(file)
        
        #Got this line from ChatGPT to simplify file reading
        public_key = public_key = ''.join([next(file).strip() for _ in range(3)])

    wallet_hash = hashlib.sha256(public_key.encode()).hexdigest()
    return wallet_hash[:16]

def getCurrentTime():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%a %b %d %H:%M:%S %Y")
    return formatted_time

def verifySignature(signature, pubKey, message):
    try:
        rsa.verify(message, signature, pubKey)
        return True
    except rsa.VerificationError as e:
        return False
    
def getBalance(wallet_tag):
    balance = 0

    with open('mempool.txt', 'r') as mempool:
        for line in mempool.readlines():
            words = line.split()
            if words[4] == wallet_tag:
                balance += int(words[2])
            if words[0] == wallet_tag:
                balance -= int(words[2])

    block_counter = 1
    while True:
        if not os.path.exists('block_' + str(block_counter) + '.txt'):
            break
        else:
            with open('block_' + str(block_counter) + '.txt', 'r') as current_block:
                for block in current_block.readlines():
                    words = block.split()
                    if len(words) > 2:
                        if words[4] == wallet_tag:
                            balance += int(words[2])
                        if words[0] == wallet_tag:
                            balance -= int(words[2])
        block_counter+=1

    return balance
    
# def findNonce(block_number, difficulty):
#     nonce = 0

#     with open('block_' + str(block_number) + '.txt', 'r') as block:
#         file_strings = block.readlines()
#         data = ''.join(file_strings[:4])
    
#     while True:
#         hash = str(hashlib.sha256((data + str(nonce)).encode()).hexdigest())
        
#         if hash[0:difficulty] == ("0"*difficulty):
#             print(data + "Nonce: " + str(nonce))
#             print(hash)
#             return nonce
#         else:
#             nonce += 1


#Print the name of the cryptocurrency
if command == 'name':
    print("MookCoin(TM)")

#Create the genesis block
if command == 'genesis':
    with open("block_0.txt","w+") as genesis:
        genesis.write("Lets go mining.")
        print("Genesis block created in 'block_0.txt'")

#Create a wallet
if command == 'generate':
    file_name = sys.argv[2]
    wallet_file = open(file_name, "w+")

    (pubkey, privkey) = rsa.newkeys(1024)

    pubkey_bytes = pubkey.save_pkcs1(format='PEM')
    privkey_bytes = privkey.save_pkcs1(format='PEM')

    pubkey_string = pubkey_bytes.decode('ascii')
    privkey_string = privkey_bytes.decode('ascii')

    wallet_file.write(pubkey_string)
    wallet_file.write(privkey_string)

    wallet_file.close()

    print("New wallet generated in '" + file_name + "' with tag " + getWalletTag(file_name))

#Give the tag of the wallet
if command == 'address':
    file_name = sys.argv[2]

    print(getWalletTag(file_name))

#Add funds to a wallet from mookie (basically the bank)
if command == 'fund':
    address = sys.argv[2]
    amount = sys.argv[3]
    file_name = sys.argv[4]

    time = getCurrentTime()

    with open(file_name, "w+") as file:
        file.write('From: mookie \n')
        file.write('To: ' + address + '\n')
        file.write("Amount: " + amount + '\n')
        file.write("Date: " + time)

    print("Funded wallet " + address + " with " + amount + " MookCoin on " + time)

#Complete a transaction between two wallets
if command == 'transfer':
    source_wallet = sys.argv[2] 
    dest_address = sys.argv[3]
    amount = sys.argv[4]
    file_name = sys.argv[5]

    time = getCurrentTime()
    source_address = getWalletTag(source_wallet)

    data = 'From: ' + source_address +'\n' + 'To: ' + dest_address + '\n' + "Amount: " + amount + '\n' + "Date: " + time + '\n'

    data_hash = data.encode()
    (pubkey, privkey) = loadWallet(source_wallet)
    signature = rsa.sign(data_hash, privkey, 'SHA-256')
    signature = signature.hex()
    
    with open(file_name, "w+") as file:
        file.write(data + '\n')
        file.write(signature)

    print(f"Transferred {amount} from {source_wallet} to {dest_address} and the statement to '{file_name}' on {time}")


#Get the balance of a wallet based on blockchain and mempool
if command == 'balance':
    wallet_tag = sys.argv[2]
    print(getBalance(wallet_tag))

#Verifies transfers and adds to mempool if valid. All verify commands of funds are valid and added to mempool.
if command == 'verify':
    wallet_file = sys.argv[2]
    transaction_statement = sys.argv[3]

    time = getCurrentTime()

    with open(transaction_statement, 'r') as file:
        file_strings = file.readlines()

        data = ''.join(file_strings[:4])

        from_statement = file_strings[0]

        source_address = getWalletTag(wallet_file)
        dest_address = file_strings[1][3:].strip()

        amount = file_strings[2][8:].strip()

        if from_statement.find('mookie') != -1:
            with open('mempool.txt', "a") as mempool:
                mempool.write("mookie transferred " + amount + " to " + dest_address + " on " + time + '\n')
            print("Any funding request (from mookie) is considered valid; written to the mempool")
        else:
            hash = data.encode()
            signature = bytes.fromhex(file_strings[5].strip())

            (pubkey, privkey) = loadWallet(wallet_file)

            if verifySignature(signature, pubkey, hash) & (getBalance(source_address) >= int(amount)):
                print("The transaction in file '" + transaction_statement + "' with wallet '" + wallet_file + "' is valid, and was added to mempool.")

                with open('mempool.txt', "a") as mempool:
                    mempool.write(source_address + " transferred " + amount + " to " + dest_address + " on " + time + '\n')
            else:
                print("The transaction in file '" + transaction_statement + "' with wallet '" + wallet_file + "' is NOT valid!")

#Command that handles the mining and thus creation of blocks.
if command == "mine":
    difficulty = int(sys.argv[2])

    block_counter = 1
    while True:
        if not os.path.exists('block_' + str(block_counter) + '.txt'):
            break
        block_counter+=1
    
    previous_hash = hashFile('block_' + str(block_counter-1) + '.txt')
    with open('block_' + str(block_counter) + '.txt', 'a') as new_block:
        new_block.write(previous_hash + '\n\n')
        
        with open('mempool.txt', 'r') as mempool:
            transactions = mempool.readlines()

        #erases contents of mempool
        open('mempool.txt', 'w').close()
        
        new_block.write("".join([line for line in transactions]))
        new_block.write('\n' + "Nonce: ")

        nonce = 0

    with open('block_' + str(block_counter) + '.txt', 'r') as block:
        file_strings = block.readlines()
        data = ''.join(file_strings)
    
    while True:
        hash = str(hashlib.sha256((data + str(nonce)).encode()).hexdigest())
        
        if hash[0:difficulty] == ("0"*difficulty):
            break
        else:
            nonce += 1

    with open('block_' + str(block_counter) + '.txt', 'a') as block:
        block.write(str(nonce))
            
    print(f"Mempool transactions were emptied into block_{block_counter}.txt, and mined with difficulty {difficulty} and nonce value of {nonce}.")

#Checks entire blockchain to ensure hashes of each block match the previous block.
if command == "validate":
    block_counter = 1
    flag = True

    while True:
        if not os.path.exists('block_' + str(block_counter) + '.txt'):
            break

        with open('block_' + str(block_counter) + '.txt', "r") as current_block:
            hash = current_block.readline().strip()
            previous_hash = hashFile('block_' + str(block_counter-1) + '.txt')

            if not hash == previous_hash:
                flag = False
                break

        block_counter+=1

    if flag :
        print("True")
    else:
        print("False")
