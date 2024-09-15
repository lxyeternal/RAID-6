# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : main.py
# @Project  : raid6
# Time      : 14/9/24 2:46 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""



# main.py

import sys
import os
from pyfinite import ffield
from raid6 import raid6_stripe, generate_parity, generate_q_parity, F
from storage_manager import store_block, retrieve_block
from utilities import read_file_to_blocks, write_blocks_to_file

# Storage configuration
DATA_DISKS = 6
PARITY_DISKS = 2
TOTAL_DISKS = DATA_DISKS + PARITY_DISKS
STORAGE_NODES = [
    {'name': 'node1', 'host': 'localhost', 'port': 5001},
    {'name': 'node2', 'host': 'localhost', 'port': 5002},
    {'name': 'node3', 'host': 'localhost', 'port': 5003},
    {'name': 'node4', 'host': 'localhost', 'port': 5004},
    {'name': 'node5', 'host': 'localhost', 'port': 5005},
    {'name': 'node6', 'host': 'localhost', 'port': 5006},
    {'name': 'parity1', 'host': 'localhost', 'port': 5007},
    {'name': 'parity2', 'host': 'localhost', 'port': 5008},
]

def main():
    # Input file path
    input_file = input("Enter the path to the input file: ").strip()
    if not os.path.isfile(input_file):
        print("Invalid file path.")
        sys.exit(1)

    # Get the block size from the user
    while True:
        block_size_input = input("Enter the block size (e.g., 1KB, 4MB): ").strip().upper()
        if block_size_input.endswith('KB'):
            block_size = int(block_size_input[:-2]) * 1024
            break
        elif block_size_input.endswith('MB'):
            block_size = int(block_size_input[:-2]) * 1024 * 1024
            break
        else:
            print("Invalid block size format. Please enter in KB or MB (e.g., 1KB, 4MB).")

    # Read the input file and divide it into blocks
    data_blocks = read_file_to_blocks(input_file, block_size)
    original_file_size = os.path.getsize(input_file)
    print(f"File '{input_file}' read successfully. Size: {original_file_size} bytes.")
    print(f"Data divided into {len(data_blocks)} blocks of size {block_size} bytes.")

    # Organize data blocks into stripes
    stripes = []
    for i in range(0, len(data_blocks), DATA_DISKS):
        stripe_data_blocks = data_blocks[i:i+DATA_DISKS]
        # Pad stripe if necessary
        if len(stripe_data_blocks) < DATA_DISKS:
            stripe_data_blocks += [bytes(block_size)] * (DATA_DISKS - len(stripe_data_blocks))
        p_parity, q_parity = raid6_stripe(stripe_data_blocks)
        stripes.append((stripe_data_blocks, p_parity, q_parity))

    print(f"Total stripes created: {len(stripes)}")

    # Store data blocks and parity blocks to storage nodes
    for stripe_index, (data_blocks, p_parity, q_parity) in enumerate(stripes):
        # Store data blocks
        for i, block in enumerate(data_blocks):
            node = STORAGE_NODES[i]
            filename = f'stripe_{stripe_index}_block_{i}'
            store_block(node, filename, block)
        # Store parity blocks
        parity_nodes = [STORAGE_NODES[-2], STORAGE_NODES[-1]]
        parity_blocks = [p_parity, q_parity]
        for node, parity_block in zip(parity_nodes, parity_blocks):
            filename = f'stripe_{stripe_index}_parity'
            store_block(node, filename, parity_block)

    print("Data stored to nodes successfully.")

    # Simulate failures
    failure_info = simulate_failures(len(stripes))

    # Retrieve and reconstruct data
    reconstructed_blocks = []
    for stripe_index in range(len(stripes)):
        data_blocks, parity_blocks, missing_indices = retrieve_data_blocks(stripe_index, block_size)
        if len(missing_indices) > 2:
            print(f"Cannot reconstruct stripe {stripe_index}: more than two missing blocks.")
            reconstructed_blocks.extend([bytes(block_size)] * DATA_DISKS)
            continue
        reconstructed_data_blocks = reconstruct_stripe(stripe_index, data_blocks, parity_blocks, missing_indices)
        reconstructed_blocks.extend(reconstructed_data_blocks[:DATA_DISKS])

    # Write the reconstructed data to the output file
    output_file = 'restored_' + os.path.basename(input_file)
    write_blocks_to_file(reconstructed_blocks, output_file, original_file_size)
    print(f"Restored file saved as '{output_file}'.")

    # Verify the restored file
    if os.path.exists(output_file) and os.path.getsize(output_file) == original_file_size:
        print("Success: The restored file matches the original file size.")
    else:
        print("Warning: The restored file does not match the original file size.")

def simulate_failures(num_stripes):
    print("Choose failure type:")
    print("A: Simulate disk failure (enter indices 0-7 for disks or parity)")
    print("B: Simulate data block corruption (enter block IDs)")

    while True:
        choice = input("Enter 'A' for disk failure or 'B' for data block corruption: ").strip().upper()
        if choice == 'A':
            # Disk failure
            print("Available disks:")
            for idx, node in enumerate(STORAGE_NODES):
                print(f"{idx}: {node['name']}")

            while True:
                try:
                    failed_nodes_input = input("Enter the indices of up to two failed disks separated by spaces (e.g., 0 6): ").strip()
                    if not failed_nodes_input:
                        failed_indices = []
                    else:
                        failed_indices = list(map(int, failed_nodes_input.strip().split()))
                    if len(failed_indices) <= 2 and all(0 <= idx < TOTAL_DISKS for idx in failed_indices):
                        failed_node_names = [STORAGE_NODES[idx]['name'] for idx in failed_indices]
                        print(f"Failed disks: {failed_node_names}")
                        return choice, failed_node_names
                    else:
                        print("Invalid input. Please enter up to two valid indices.")
                except ValueError:
                    print("Invalid input. Please enter numeric indices.")
        elif choice == 'B':
            # Data block corruption
            block_list = []
            block_id = 0
            print("Available data blocks:")
            for stripe_index in range(num_stripes):
                for i in range(DATA_DISKS):
                    node_name = STORAGE_NODES[i]['name']
                    print(f"Block ID {block_id}: Stripe {stripe_index}, Node {node_name}, Data Block")
                    block_list.append((stripe_index, i, node_name, 'data'))
                    block_id += 1
                # Parity blocks
                print(f"Block ID {block_id}: Stripe {stripe_index}, Node {STORAGE_NODES[-2]['name']}, P Parity")
                block_list.append((stripe_index, 'parity1', STORAGE_NODES[-2]['name'], 'P'))
                block_id += 1
                print(f"Block ID {block_id}: Stripe {stripe_index}, Node {STORAGE_NODES[-1]['name']}, Q Parity")
                block_list.append((stripe_index, 'parity2', STORAGE_NODES[-1]['name'], 'Q'))
                block_id += 1

            while True:
                try:
                    corrupted_blocks_input = input("Enter the block IDs to corrupt, separated by spaces: ").strip()
                    if not corrupted_blocks_input:
                        corrupted_block_ids = []
                    else:
                        corrupted_block_ids = list(map(int, corrupted_blocks_input.strip().split()))
                    if all(0 <= idx < len(block_list) for idx in corrupted_block_ids):
                        print(f"Corrupted block IDs: {corrupted_block_ids}")
                        return choice, [block_list[idx] for idx in corrupted_block_ids]
                    else:
                        print("Invalid input. Please enter valid block IDs.")
                except ValueError:
                    print("Invalid input. Please enter numeric block IDs.")
        else:
            print("Invalid choice. Please enter 'A' or 'B'.")

def retrieve_data_blocks(stripe_index, block_size):
    data_blocks = []
    missing_indices = []
    for i in range(DATA_DISKS):
        node = STORAGE_NODES[i]
        filename = f'stripe_{stripe_index}_block_{i}'
        block = retrieve_block(node, filename)
        if block is None:
            data_blocks.append(None)
            missing_indices.append(i)
        else:
            data_blocks.append(block)
    # Retrieve parity blocks
    parity_blocks = []
    for node in STORAGE_NODES[-2:]:
        filename = f'stripe_{stripe_index}_parity'
        block = retrieve_block(node, filename)
        parity_blocks.append(block)
    return data_blocks, parity_blocks, missing_indices

def reconstruct_stripe(stripe_index, data_blocks, parity_blocks, missing_indices):
    p_parity, q_parity = parity_blocks
    block_size = len(p_parity)
    failed_disks_in_stripe = set(missing_indices)

    # Check if the number of failed disks in the stripe exceeds two
    if len(failed_disks_in_stripe) > 2:
        print(f"Cannot recover stripe {stripe_index}, more than two disks have failed.")
        return [bytes(block_size)] * DATA_DISKS  # Placeholder zeros

    num_missing_data = len(missing_indices)
    if num_missing_data == 0:
        # No data disks are missing
        return data_blocks

    elif num_missing_data == 1:
        # One data disk is missing
        missing_index = missing_indices[0]
        reconstructed_block = bytearray(block_size)
        for j in range(block_size):
            p_parity_byte = p_parity[j]
            reconstructed_byte = p_parity_byte
            for i, block in enumerate(data_blocks):
                if i != missing_index and block is not None:
                    reconstructed_byte ^= block[j]
            reconstructed_block[j] = reconstructed_byte
        data_blocks[missing_index] = bytes(reconstructed_block)
        print(f"Reconstructed data block at index {missing_index} in stripe {stripe_index}")
        return data_blocks

    elif num_missing_data == 2:
        # Two data disks are missing
        m1, m2 = missing_indices
        reconstructed_block1 = bytearray(block_size)
        reconstructed_block2 = bytearray(block_size)

        for j in range(block_size):
            p_parity_byte = p_parity[j]
            q_parity_byte = q_parity[j]

            sum_p = p_parity_byte
            sum_q = q_parity_byte

            for idx, block in enumerate(data_blocks):
                if idx != m1 and idx != m2 and block is not None:
                    block_byte = block[j]
                    sum_p ^= block_byte
                    multiplier = idx + 1
                    sum_q = F.Add(sum_q, F.Multiply(block_byte, multiplier))

            c1 = m1 + 1
            c2 = m2 + 1

            coeff = F.Add(c1, c2)
            rhs = F.Add(sum_q, F.Multiply(c2, sum_p))
            if coeff == 0:
                print(f"Cannot recover byte {j} in stripe {stripe_index}, equations cannot be solved.")
                reconstructed_block1[j] = 0
                reconstructed_block2[j] = 0
                continue

            D_m1_byte = F.Divide(rhs, coeff)
            D_m2_byte = F.Add(D_m1_byte, sum_p)

            reconstructed_block1[j] = D_m1_byte
            reconstructed_block2[j] = D_m2_byte

        data_blocks[m1] = bytes(reconstructed_block1)
        data_blocks[m2] = bytes(reconstructed_block2)
        print(f"Reconstructed data blocks at indices {m1} and {m2} in stripe {stripe_index}")
        return data_blocks

if __name__ == "__main__":
    main()
