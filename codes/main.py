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



# codes/main.py

import sys
from pyfinite import ffield
from raid6 import raid6_stripe, reconstruct_data, F
from storage_manager import store_to_nodes, read_from_nodes
from utilities import string_to_binary, binary_to_string, ensure_storage_dir, clean_storage_nodes

# Storage configuration
DATA_DISKS = 6
PARITY_DISKS = 2
TOTAL_DISKS = DATA_DISKS + PARITY_DISKS
STORAGE_NODES = [f"node{i+1}" for i in range(DATA_DISKS)] + ["parity1", "parity2"]
STORAGE_DIR = '../storage'  # Adjust the path as needed

def simulate_failures(stripes):
    """Simulates disk failures or data block corruption based on user input."""
    print("Choose failure type:")
    print("A: Simulate disk failure (enter indices 0-7 for disks or parity)")
    print("B: Simulate data block corruption (enter block IDs)")

    while True:
        choice = input("Enter 'A' for disk failure or 'B' for data block corruption: ").strip().upper()
        if choice == 'A':
            # Disk failure
            print("Available disks:")
            for idx, node in enumerate(STORAGE_NODES):
                print(f"{idx}: {node}")

            while True:
                try:
                    failed_nodes_input = input("Enter the indices of up to two failed disks separated by spaces (e.g., 0 6): ").strip()
                    if not failed_nodes_input:
                        failed_indices = []
                    else:
                        failed_indices = list(map(int, failed_nodes_input.strip().split()))
                    if len(failed_indices) <= 2 and all(0 <= idx < TOTAL_DISKS for idx in failed_indices):
                        failed_node_names = [STORAGE_NODES[idx] for idx in failed_indices]
                        print(f"Failed disks: {failed_node_names}")
                        return choice, failed_node_names
                    else:
                        print("Invalid input. Please enter less three valid indices.")
                except ValueError:
                    print("Invalid input. Please enter numeric indices.")
        elif choice == 'B':
            # Data block corruption
            # Display all block IDs with corresponding nodes and stripes
            block_list = []
            block_id = 0
            print("Available data blocks:")
            for stripe_index, (data_blocks, p_parity, q_parity) in enumerate(stripes):
                for i in range(DATA_DISKS):
                    node_name = STORAGE_NODES[i]
                    print(f"Block ID {block_id}: Stripe {stripe_index}, Node {node_name}, Data Block")
                    block_list.append((stripe_index, i, node_name, 'data'))
                    block_id += 1
                # Parity blocks
                print(f"Block ID {block_id}: Stripe {stripe_index}, Node parity1, P Parity")
                block_list.append((stripe_index, 'parity1', 'parity1', 'P'))
                block_id += 1
                print(f"Block ID {block_id}: Stripe {stripe_index}, Node parity2, Q Parity")
                block_list.append((stripe_index, 'parity2', 'parity2', 'Q'))
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

def apply_failures(node_data, failure_info):
    """Applies the simulated failures to the node data."""
    choice, failure_detail = failure_info
    failed_nodes = set()
    if choice == 'A':
        failed_nodes.update(failure_detail)
        # Remove failed nodes
        for node in failed_nodes:
            node_data[node] = None
    elif choice == 'B':
        for stripe_num, pos, node_name, block_type in failure_detail:
            if block_type == 'data':
                if node_data[node_name] is not None:
                    node_data[node_name][stripe_num] = None
                print(f"Corrupted data block at index {pos} in stripe {stripe_num}.")
            elif block_type == 'P':
                if node_data['parity1'] is not None:
                    node_data['parity1'][stripe_num] = None
                print(f"Corrupted P parity in stripe {stripe_num}.")
            elif block_type == 'Q':
                if node_data['parity2'] is not None:
                    node_data['parity2'][stripe_num] = None
                print(f"Corrupted Q parity in stripe {stripe_num}.")
            failed_nodes.add(node_name)
    return failed_nodes

def main():
    ensure_storage_dir(STORAGE_DIR)
    clean_storage_nodes(STORAGE_NODES, STORAGE_DIR)

    # Input string
    # original_string = "剣斉万里の長城、建来，Цзянь Лай, Меч Ци Великой Стены，Jianlai, 검기의 만리장성，使用这个修改后的代码,程序运行时会提示用户输入一个字符串,然后使用这个输入的字符串进行RAID6的模拟和数据恢复过程。这样,您就可以测试不同长度和内容的字符串在RAID6系统中的表现了，english"
    original_string = input("Please input a string: ")

    # Convert string to binary
    binary_data = string_to_binary(original_string)
    print(f"Original string: {original_string}")
    print(f"Binary data: {binary_data}")

    # Perform RAID-6 striping and generate parity
    stripes = raid6_stripe(binary_data)
    print(f"\nData blocks and parity for each stripe:")
    for idx, (data_blocks, p_parity, q_parity) in enumerate(stripes):
        print(f"Stripe {idx}:")
        print(f"  Data blocks: {data_blocks}")
        print(f"  P Parity: {p_parity}")
        print(f"  Q Parity: {q_parity}")

    # Store data to nodes
    store_to_nodes(stripes, STORAGE_NODES, STORAGE_DIR)

    # Simulate failures
    failure_info = simulate_failures(stripes)

    # Read data from nodes
    node_data = read_from_nodes(STORAGE_NODES, STORAGE_DIR)

    # Apply failures to node data
    failed_nodes = apply_failures(node_data, failure_info)

    # Rebuild data
    restored_data_blocks = reconstruct_data(stripes, node_data, failed_nodes, F)

    # Reconstruct the data
    restored_binary_data = ''.join(restored_data_blocks)
    restored_string = binary_to_string(restored_binary_data)
    print(f"\nRestored string: {restored_string}")

    # Output the restored data on all disks
    print("\nRestored data on all disks:")
    for idx, block in enumerate(restored_data_blocks):
        print(f"Block {idx}: {block}")

if __name__ == "__main__":
    main()
