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


# codes/utilities.py

import os

def string_to_binary(input_string):
    """Converts a Unicode string to its binary representation."""
    # Encode the string to bytes using UTF-8
    byte_data = input_string.encode('utf-8')
    # Convert each byte to its binary representation
    binary_string = ''.join(format(byte, '08b') for byte in byte_data)
    return binary_string

def binary_to_string(binary_string):
    """Converts a binary string back to a Unicode string."""
    # Split the binary string into bytes (8 bits each)
    byte_list = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
    # Convert binary bytes to integers
    byte_values = [int(byte, 2) for byte in byte_list]
    # Convert integers to bytes
    byte_data = bytes(byte_values)
    # Decode bytes to string using UTF-8
    try:
        return byte_data.decode('utf-8')
    except UnicodeDecodeError:
        return ''  # Return empty string if decoding fails

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
