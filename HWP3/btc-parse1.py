# CS 4501 HW 3 - Bitcoin Parsing
# mvy3ns

import json, sys, datetime, hashlib


#helper function for BTC data type compcact size

def decodeCompactSize(input):
    decimal = int.from_bytes(input[0:1], 'little')
    bytes = 1

    if decimal < 253:
        val = decimal
    elif decimal == 253:
        #read next two bytes
        val = int.from_bytes(input[1:3], 'little')
        bytes = 3
    elif decimal == 254:
        #read next four bytes
        val = int.from_bytes(input[1:5], 'little')
        bytes = 5
    elif decimal == 255:
        #read next eight bytes
        val = int.from_bytes(input[1:], 'little')
        bytes = 9
    else:
        val = 'ERROR'

    return val, bytes

#
#
# START OF THE ACTUAL PARSING

file_name = sys.argv[1]

with open(file_name, "rb") as file:
    blocks = 0
    prev_time = 0
    prev_block_hash = ""

    block_data = []

    while (True):
        current_block = {}
        current_block.update({"height": blocks}) 

        #---------------------PREAMBLE--------------------------

        #ERROR CHECK NUMBER 1
        magic_num = file.read(4).hex()
        if not magic_num == "f9beb4d9":
            print("error 1 block", blocks)
            break

        block_size = int.from_bytes(file.read(4), 'little')

        block_pointer = 0
        current_block_bytes = file.read(block_size)

        #-------------------END PREAMBLE------------------------

        #---------------------HEADER--------------------------

        # store previous block data for checking hash with next block
        header = current_block_bytes[block_pointer:block_pointer+80]
        prev_header_data = header
        block_pointer+=80

        #ERROR CHECK NUMBER 2
        version = int.from_bytes(header[:4], 'little')
        # print(version)
        current_block.update({"version": version})
        if not version == 1:
            print("error 2 block", blocks)
            break

        #previous hash stored in the header
        prev_hash = header[4:36][::-1].hex()
        
        #ERROR CHECK NUMBER 3
        if (blocks > 0) & (not prev_hash == prev_block_hash):
            print('error 3 block', blocks)
            break

        #taking double hash of previous blocks header to be checked with next block
        prev_block_hash = hashlib.sha256(hashlib.sha256(prev_header_data).digest()).digest()[::-1].hex()

        current_block.update({"previous_hash": prev_hash})

        #ERROR CHECK NUMBER 6
        merkle_root = header[36:68][::-1].hex()
        current_block.update({"merkle_hash": merkle_root})

        #ERROR CHECK NUMBER 4
        time = int.from_bytes(header[68:72], 'little')
        current_block.update({"timestamp": time})
        difference = time - prev_time
        if (blocks > 0) & (difference < -7200):
            print("error 4 block", blocks)
            break
        
        prev_time = time

        date_time = datetime.datetime.fromtimestamp(time)
        formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')
        current_block.update({"timestamp_readable": formatted_date_time})

        n_bits = header[72:76][::-1].hex()
        current_block.update({"nbits": n_bits})

        nonce = int.from_bytes(header[76:], 'little')
        current_block.update({"nonce": nonce})

        #-------------------END HEADER------------------------

        txn_count, bytes = decodeCompactSize(current_block_bytes[block_pointer:block_pointer+9])
        block_pointer+=bytes
        current_block.update({"txn_count": txn_count})

        txn_array = []
        txn_hashes = []
        for i in range(txn_count):
            transaction = {}

            txn_start_pos = block_pointer

            #ERROR CHECK NUMBER 5
            txn_version = int.from_bytes(current_block_bytes[block_pointer:block_pointer+4], 'little')
            block_pointer+=4
            transaction.update({"version": txn_version})
            if not txn_version == 1:
                print("error 5 block", blocks)
                break

            txn_in_count, bytes = decodeCompactSize(current_block_bytes[block_pointer:block_pointer+9])
            block_pointer+=bytes
            transaction.update({"txn_in_count": txn_in_count})

            txn_in_array = []
            for x in range(txn_in_count):
                txn_in = {}

                utxo = current_block_bytes[block_pointer:block_pointer+32][::-1].hex()
                block_pointer+=32
                txn_in.update({"txn_hash": utxo})

                utxo_i = int.from_bytes(current_block_bytes[block_pointer:block_pointer+4], 'little')
                block_pointer+=4
                txn_in.update({"index": utxo_i})

                in_script_size, bytes = decodeCompactSize(current_block_bytes[block_pointer:block_pointer+9])
                block_pointer+=bytes
                txn_in.update({"input_script_size": in_script_size})

                input_script = current_block_bytes[block_pointer:block_pointer+in_script_size].hex()
                block_pointer+=in_script_size
                txn_in.update({"input_script_bytes": input_script})

                sequence = int.from_bytes(current_block_bytes[block_pointer:block_pointer+4], 'little')
                block_pointer+=4
                txn_in.update({"sequence": sequence})

                txn_in_array.append(txn_in)
            # ------ END TXN INPUT LOOP
            transaction.update({"txn_inputs": txn_in_array})

            txn_out_count, bytes = decodeCompactSize(current_block_bytes[block_pointer:block_pointer+9])
            block_pointer+=bytes
            transaction.update({"txn_out_count": txn_out_count})

            txn_out_array = []
            for y in range(txn_out_count):
                txn_out = {}

                satoshis = int.from_bytes(current_block_bytes[block_pointer:block_pointer+8], 'little')
                block_pointer+=8
                txn_out.update({"satoshis": satoshis})

                out_script_size, bytes = decodeCompactSize(current_block_bytes[block_pointer:block_pointer+9])
                block_pointer+=bytes
                txn_out.update({"output_script_size": out_script_size})

                output_script = current_block_bytes[block_pointer:block_pointer+out_script_size].hex()
                block_pointer+=out_script_size
                txn_out.update({"output_script_bytes": output_script})

                txn_out_array.append(txn_out)
            # ------ END TXN OUT LOOP
            transaction.update({"txn_outputs": txn_out_array})

            lock_time = int.from_bytes(current_block_bytes[block_pointer:block_pointer+4], 'little')
            block_pointer+=4
            transaction.update({"lock_time": lock_time})

            txn_array.append(transaction)

            block_data.append(current_block)

            txn_data = current_block_bytes[txn_start_pos:block_pointer]
            txn_hashes.append(hashlib.sha256(hashlib.sha256(txn_data).digest()).digest())
        # ------ END TXN LOOP
            
        #outer loop error check to ensure blockchain loop is broken
        if not txn_version == 1:
            break

        #ERROR 6 MERKLE TREE CHECK
        if (len(txn_hashes) == 1):
            if (not txn_hashes[0][::-1].hex() == merkle_root):
                print("error 6 block", blocks)
                break
        else:
            merkle_tree = []
            while(not len(merkle_tree) == 1):
                merkle_tree = []
                i = 0
                while i < len(txn_hashes):
                    if (i+1 < len(txn_hashes)):
                        next_node = txn_hashes[i] + txn_hashes[i+1]
                        i+=2
                    else:
                        next_node = txn_hashes[i] + txn_hashes[i]
                        i+=1
                    new_hash = hashlib.sha256(hashlib.sha256(next_node).digest()).digest()
                    merkle_tree.append(new_hash)
                    
                txn_hashes = merkle_tree
            if (not merkle_tree[0][::-1].hex() == merkle_root):
                print("error 6 block", blocks)
                break

        current_block.update({"transactions": txn_array})

        blocks+=1

        if blocks % 1000 == 0:
            print(blocks)
    # ----- END BLOCKCHAIN LOOP
    
    print(f"no errors {blocks} blocks")

    #JSON output
    with open(f"{file_name}.json", 'a') as json_file:
        json.dump({"blocks": block_data, "height": blocks}, json_file, indent=4)
