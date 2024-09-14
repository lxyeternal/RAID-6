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



# codes/raid6.py

from pyfinite import ffield

# Initialize GF(2^8) field
F = ffield.FField(8)

DATA_DISKS = 6
PARITY_DISKS = 2  # P and Q parity
TOTAL_DISKS = DATA_DISKS + PARITY_DISKS

def generate_parity(data_blocks):
    """Generates the P parity for a set of data blocks using bitwise XOR."""
    p_parity = int(data_blocks[0], 2)
    for block in data_blocks[1:]:
        p_parity ^= int(block, 2)
    return format(p_parity, '08b')

def generate_q_parity(data_blocks):
    """Generates the Q parity for a set of data blocks using GF(2^8) multiplication."""
    q_parity = 0
    for i, block in enumerate(data_blocks):
        block_byte = int(block, 2)
        multiplier = i + 1
        q_parity = F.Add(q_parity, F.Multiply(block_byte, multiplier))
    return format(q_parity, '08b')

def raid6_stripe(binary_data, stripe_size=8):
    """Splits binary data into stripes and generates parity blocks."""
    # Split the binary data into blocks of 8 bits (1 byte)
    data_blocks = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]

    # Pad the last data block if it's not full
    if len(data_blocks[-1]) < 8:
        data_blocks[-1] += '0' * (8 - len(data_blocks[-1]))

    # Split data blocks into stripes
    stripes = []
    for i in range(0, len(data_blocks), DATA_DISKS):
        stripe_data_blocks = data_blocks[i:i+DATA_DISKS]
        # Pad stripe if necessary
        if len(stripe_data_blocks) < DATA_DISKS:
            stripe_data_blocks += ['0' * 8] * (DATA_DISKS - len(stripe_data_blocks))
        p_parity = generate_parity(stripe_data_blocks)
        q_parity = generate_q_parity(stripe_data_blocks)
        stripes.append((stripe_data_blocks, p_parity, q_parity))
    return stripes

def reconstruct_data(stripes, node_data, failed_nodes, F):
    """Reconstructs missing or corrupted data using RAID-6 algorithms."""
    restored_data_blocks = []

    for stripe_index, (original_data_blocks, p_parity, q_parity) in enumerate(stripes):
        data_blocks = []
        missing_indices = []
        missing_parity = []
        failed_disks_in_stripe = set()

        # Initialize data blocks
        for i in range(DATA_DISKS):
            node_name = f"node{i+1}"
            if node_name in failed_nodes:
                data_blocks.append(None)
                missing_indices.append(i)
                failed_disks_in_stripe.add(node_name)
            else:
                block = node_data[node_name][stripe_index]
                data_blocks.append(block)

        # Handle parity blocks
        if 'parity1' in failed_nodes:
            p_parity = None
            missing_parity.append('P')
            failed_disks_in_stripe.add('parity1')
        else:
            p_parity = node_data['parity1'][stripe_index]

        if 'parity2' in failed_nodes:
            q_parity = None
            missing_parity.append('Q')
            failed_disks_in_stripe.add('parity2')
        else:
            q_parity = node_data['parity2'][stripe_index]

        # Check if the number of failed disks in the stripe exceeds two
        if len(failed_disks_in_stripe) > 2:
            print(f"Cannot recover stripe {stripe_index}, more than two disks have failed.")
            restored_data_blocks.extend(['0' * 8] * DATA_DISKS)  # Placeholder zeros
            continue  # Skip this stripe

        # Recompute missing parity disks if necessary
        if p_parity is None:
            p_parity = generate_parity([block if block is not None else '0' * 8 for block in data_blocks])
        if q_parity is None:
            q_parity = generate_q_parity([block if block is not None else '0' * 8 for block in data_blocks])

        # Perform recovery based on the number of missing data blocks
        num_missing_data = len(missing_indices)
        if num_missing_data == 0:
            # No data disks are missing
            restored_data_blocks.extend(data_blocks)
            continue

        elif num_missing_data == 1:
            # One data disk is missing
            missing_index = missing_indices[0]
            p_parity_byte = int(p_parity, 2)
            reconstructed_byte = p_parity_byte
            for i, block in enumerate(data_blocks):
                if i != missing_index and block is not None:
                    reconstructed_byte ^= int(block, 2)
            data_blocks[missing_index] = format(reconstructed_byte, '08b')
            print(f"Reconstructed data block at index {missing_index} in stripe {stripe_index}: {data_blocks[missing_index]}")

        elif num_missing_data == 2:
            # Two data disks are missing
            m1, m2 = missing_indices

            p_parity_byte = int(p_parity, 2)
            q_parity_byte = int(q_parity, 2)

            # Sum over known data blocks for P and Q parity
            sum_p = p_parity_byte
            sum_q = q_parity_byte

            for idx, block in enumerate(data_blocks):
                if idx != m1 and idx != m2 and block is not None:
                    block_byte = int(block, 2)
                    sum_p ^= block_byte
                    multiplier = idx + 1
                    sum_q = F.Add(sum_q, F.Multiply(block_byte, multiplier))

            c1 = m1 + 1
            c2 = m2 + 1

            # Solve for D_m1 and D_m2
            coeff = F.Add(c1, c2)
            rhs = F.Add(sum_q, F.Multiply(c2, sum_p))
            if coeff == 0:
                print(f"Cannot recover stripe {stripe_index}, equations cannot be solved.")
                restored_data_blocks.extend(['0' * 8] * DATA_DISKS)  # Placeholder zeros
                continue
            D_m1_byte = F.Divide(rhs, coeff)
            D_m2_byte = F.Add(D_m1_byte, sum_p)

            data_blocks[m1] = format(D_m1_byte, '08b')
            data_blocks[m2] = format(D_m2_byte, '08b')
            print(f"Reconstructed data block at index {m1} in stripe {stripe_index}: {data_blocks[m1]}")
            print(f"Reconstructed data block at index {m2} in stripe {stripe_index}: {data_blocks[m2]}")

        restored_data_blocks.extend(data_blocks)
    return restored_data_blocks
