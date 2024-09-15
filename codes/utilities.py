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
    with open(file_path, 'rb') as f:
        data = f.read()
    blocks = [data[i:i+block_size] for i in range(0, len(data), block_size)]
    if len(blocks[-1]) < block_size:
        blocks[-1] += b'\x00' * (block_size - len(blocks[-1]))
    return blocks, len(data)

def write_blocks_to_file(blocks, file_path, original_size):
    with open(file_path, 'wb') as f:
        for block in blocks:
            f.write(block)
        f.truncate(original_size)  # Ensure we don't write extra padding