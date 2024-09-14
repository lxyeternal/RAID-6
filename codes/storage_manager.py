# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : storage_manager.py
# @Project  : raid6
# Time      : 14/9/24 2:46 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""



# codes/storage_manager.py

import os

def store_to_nodes(stripes, storage_nodes, storage_dir):
    """Stores data blocks and parity blocks to their respective nodes."""
    node_files = {node: open(os.path.join(storage_dir, node), 'w') for node in storage_nodes}

    for stripe_index, (data_blocks, p_parity, q_parity) in enumerate(stripes):
        for i, block in enumerate(data_blocks):
            node_name = f"node{i+1}"
            node_files[node_name].write(block + '\n')
        # Write parity blocks
        node_files['parity1'].write(p_parity + '\n')
        node_files['parity2'].write(q_parity + '\n')

    # Close all files
    for f in node_files.values():
        f.close()

def read_from_nodes(storage_nodes, storage_dir):
    """Reads data from storage nodes."""
    node_data = {node: [] for node in storage_nodes}

    # Read data from each node file
    for node in storage_nodes:
        node_path = os.path.join(storage_dir, node)
        if os.path.exists(node_path):
            with open(node_path, 'r') as f:
                node_data[node] = f.read().strip().split('\n')
        else:
            node_data[node] = None  # Node has failed

    return node_data
