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

import os
import json
from storage_manager import store_block, retrieve_block, check_node_online
from utilities import read_file_to_blocks, write_blocks_to_file
from raid6 import raid6_stripe, reconstruct_stripe

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


def parse_block_size(size_str):
    size_str = size_str.upper()
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    else:
        raise ValueError("Invalid block size format. Use KB or MB (e.g., 64KB, 1MB)")


def store_raid6(blocks, original_size, original_filename, block_size):
    metadata = {
        'original_filename': original_filename,
        'original_size': original_size,
        'total_stripes': len(blocks) // DATA_DISKS + (1 if len(blocks) % DATA_DISKS else 0),
        'block_size': block_size
    }

    print(f"Storing metadata: {metadata}")
    metadata_json = json.dumps(metadata)
    for node in STORAGE_NODES:
        store_block(node, 'metadata', metadata_json.encode())

    for stripe_index, stripe_blocks in enumerate(chunks(blocks, DATA_DISKS)):
        print(f"Processing stripe {stripe_index}")
        while len(stripe_blocks) < DATA_DISKS:
            stripe_blocks.append(b'\x00' * block_size)

        p_parity, q_parity = raid6_stripe(stripe_blocks)

        for i, block in enumerate(stripe_blocks + [p_parity, q_parity]):
            filename = f'stripe_{stripe_index}_block_{i}'
            store_block(STORAGE_NODES[i], filename, block)

        print(f"Stored stripe {stripe_index}")

    print(f"Total stripes stored: {metadata['total_stripes']}")


def recover_data():
    online_nodes = [node for node in STORAGE_NODES if check_node_online(node)]
    print(f"Online nodes: {[node['name'] for node in online_nodes]}")
    if len(online_nodes) < DATA_DISKS:
        print(f"Error: Not enough online nodes to recover data. Online nodes: {len(online_nodes)}")
        return

    metadata = None
    for node in online_nodes:
        try:
            metadata_json = retrieve_block(node, 'metadata')
            if metadata_json:
                metadata = json.loads(metadata_json.decode())
                print(f"Retrieved metadata from node {node['name']}")
                break
        except Exception as e:
            print(f"Failed to retrieve metadata from node {node['name']}: {str(e)}")
            continue

    if not metadata:
        print("Error: Could not retrieve metadata from any node")
        return

    print(f"Metadata: {metadata}")
    total_stripes = metadata['total_stripes']
    original_size = metadata['original_size']
    original_filename = metadata['original_filename']
    block_size = metadata['block_size']

    reconstructed_blocks = []

    for stripe_index in range(total_stripes):
        print(f"Processing stripe {stripe_index}")
        stripe_blocks = []
        missing_indices = []
        for i, node in enumerate(STORAGE_NODES):
            if node in online_nodes:
                block = retrieve_block(node, f'stripe_{stripe_index}_block_{i}')
                if block is None:
                    print(f"Failed to retrieve block from online node {node['name']}")
                    missing_indices.append(i)
                else:
                    stripe_blocks.append(block)
            else:
                print(f"Node {node['name']} is offline")
                missing_indices.append(i)
                stripe_blocks.append(None)

        print(f"Missing indices for stripe {stripe_index}: {missing_indices}")

        try:
            reconstructed_stripe = reconstruct_stripe(stripe_blocks[:DATA_DISKS], stripe_blocks[DATA_DISKS],
                                                      stripe_blocks[DATA_DISKS + 1], missing_indices)
            reconstructed_blocks.extend(reconstructed_stripe[:DATA_DISKS])
            print(f"Successfully reconstructed stripe {stripe_index}")
        except Exception as e:
            print(f"Error reconstructing stripe {stripe_index}: {str(e)}")
            return

    output_file = f'recovered_{original_filename}'
    write_blocks_to_file(reconstructed_blocks, output_file, original_size)
    print(f"Recovered file saved as '{output_file}'")
    print(f"Original size: {original_size}, Recovered size: {os.path.getsize(output_file)}")


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


if __name__ == "__main__":
    while True:
        choice = input("Choose operation: 1. Store file  2. Recover data  3. Exit ")
        if choice == '1':
            file_path = input("Enter the file path to store: ")
            if not os.path.exists(file_path):
                print("Error: File does not exist")
            else:
                block_size_input = input("Enter block size (e.g., 64KB, 1MB): ")
                try:
                    block_size = parse_block_size(block_size_input)
                    blocks, file_size = read_file_to_blocks(file_path, block_size)
                    original_filename = os.path.basename(file_path)
                    store_raid6(blocks, file_size, original_filename, block_size)
                    print(f"File '{original_filename}' has been successfully stored in the RAID-6 system.")
                except ValueError as e:
                    print(f"Error: {str(e)}")
        elif choice == '2':
            recover_data()
        elif choice == '3':
            break
        else:
            print("Invalid choice")