# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : utilities.py
# @Project  : raid6
# Time      : 14/9/24 2:45 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""


# utilities.py

import os

def read_file_to_blocks(file_path, block_size):
    """Reads a file and splits it into blocks of specified size."""
    with open(file_path, 'rb') as f:
        data = f.read()
    blocks = [data[i:i+block_size] for i in range(0, len(data), block_size)]
    # Pad the last block if necessary
    if len(blocks[-1]) < block_size:
        blocks[-1] += bytes(block_size - len(blocks[-1]))
    return blocks

def write_blocks_to_file(blocks, file_path, original_size):
    """Writes a list of blocks to a file, trimming any padding."""
    with open(file_path, 'wb') as f:
        data = b''.join(blocks)
        f.write(data[:original_size])  # Trim padding to match original size

def ensure_storage_dir(storage_dir):
    """Ensures that the storage directory exists."""
    if not os.path.exists(storage_dir):
        os.makedirs(storage_dir)

def clean_storage_nodes(storage_nodes, storage_dir):
    """Cleans up the storage nodes by deleting existing data files."""
    for node in storage_nodes:
        node_path = os.path.join(storage_dir, node)
        if os.path.exists(node_path):
            os.remove(node_path)

