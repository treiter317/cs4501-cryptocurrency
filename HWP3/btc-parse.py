
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

        #-------------------END PREAMBLE------------------------

        #---------------------HEADER--------------------------

        # store previous block data for checking hash with next block
        header = file.read(80)
        prev_header_data = header

        #ERROR CHECK NUMBER 2
        version = int.from_bytes(header[:4], 'little')
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
        #TODO: check if merkle root is correct
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

        current_position = file.tell()
        txn_count, bytes = decodeCompactSize(file.read(9))
        current_block.update({"txn_count": txn_count})
        file.seek(current_position+bytes)

        txn_array = []
        txn_hashes = []
        for i in range(txn_count):
            transaction = {}

            transaction_start_pos = file.tell()

            #ERROR CHECK NUMBER 5
            txn_version = int.from_bytes(file.read(4), 'little')
            transaction.update({"version": txn_version})
            if not txn_version == 1:
                print("error 5 block", blocks)
                break

            current_position = file.tell()
            txn_in_count, bytes = decodeCompactSize(file.read(9))
            transaction.update({"txn_in_count": txn_in_count})
            file.seek(current_position+bytes)

            txn_in_array = []
            for x in range(txn_in_count):
                txn_in = {}

                utxo = file.read(32)[::-1].hex()
                txn_in.update({"txn_hash": utxo})

                utxo_i = int.from_bytes(file.read(4), 'little')
                txn_in.update({"index": utxo_i})

                current_position = file.tell()
                in_script_size, bytes = decodeCompactSize(file.read(9))
                txn_in.update({"input_script_size": in_script_size})
                file.seek((current_position+bytes))

                input_script = file.read(in_script_size).hex()
                txn_in.update({"input_script_bytes": input_script})

                sequence = int.from_bytes(file.read(4), 'little')
                txn_in.update({"sequence": sequence})

                txn_in_array.append(txn_in)
            # ------ END TXN INPUT LOOP
            transaction.update({"txn_inputs": txn_in_array})

            current_position = file.tell()
            txn_out_count, bytes = decodeCompactSize(file.read(9))
            transaction.update({"txn_out_count": txn_out_count})
            file.seek(current_position+bytes)

            txn_out_array = []
            for y in range(txn_out_count):
                txn_out = {}

                satoshis = int.from_bytes(file.read(8), 'little')
                txn_out.update({"satoshis": satoshis})

                current_position = file.tell()
                out_script_size, bytes = decodeCompactSize(file.read(9))
                txn_out.update({"output_script_size": out_script_size})
                file.seek(current_position+bytes)

                output_script = file.read(out_script_size).hex()
                txn_out.update({"output_script_bytes": output_script})

                txn_out_array.append(txn_out)
            # ------ END TXN OUT LOOP
            transaction.update({"txn_outputs": txn_out_array})

            lock_time = int.from_bytes(file.read(4), 'little')
            transaction.update({"lock_time": lock_time})

            txn_array.append(transaction)

            block_data.append(current_block)

            transaction_end_pos = file.tell()
            file.seek(transaction_start_pos)
            txn_data = file.read(transaction_end_pos-transaction_start_pos)
            txn_hashes.append(hashlib.sha256(hashlib.sha256(txn_data).digest()).digest())
            file.seek(transaction_end_pos)
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

        #checks end of file or continues to next block
        current_position = file.tell()
        if not file.read(1):
            print(f"no errors {blocks} blocks")
            break
        else:
            file.seek(current_position)
    # ----- END BLOCKCHAIN LOOP
            
    #JSON output
    with open(f"{file_name}.json", 'a') as json_file:
        json.dump({"blocks": block_data, "height": blocks}, json_file, indent=4)
