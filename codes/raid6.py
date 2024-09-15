# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : raid6.py
# @Project  : raid6
# Time      : 14/9/24 2:46 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""



# raid6.py

from pyfinite import ffield

# Initialize GF(2^8) field
F = ffield.FField(8)

def generate_parity(data_blocks):
    """Generates P parity (XOR of all data blocks)."""
    p_parity = data_blocks[0]
    for block in data_blocks[1:]:
        p_parity = bytes([b1 ^ b2 for b1, b2 in zip(p_parity, block)])
    return p_parity

def generate_q_parity(data_blocks):
    """Generates Q parity using Reed-Solomon coding over GF(2^8)."""
    block_size = len(data_blocks[0])
    q_parity = bytearray(block_size)
    for i, block in enumerate(data_blocks):
        multiplier = i + 1
        for j in range(block_size):
            product = F.Multiply(block[j], multiplier)
            q_parity[j] = F.Add(q_parity[j], product)
    return bytes(q_parity)

def raid6_stripe(data_blocks):
    """Generates parity blocks for each stripe."""
    p_parity = generate_parity(data_blocks)
    q_parity = generate_q_parity(data_blocks)
    return p_parity, q_parity
