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

F = ffield.FField(8)


def generate_parity(data_blocks):
    p_parity = bytearray(len(data_blocks[0]))
    for block in data_blocks:
        for i in range(len(block)):
            p_parity[i] ^= block[i]
    return bytes(p_parity)


def generate_q_parity(data_blocks):
    q_parity = bytearray(len(data_blocks[0]))
    for i, block in enumerate(data_blocks):
        factor = field_pow(2, i)
        for j in range(len(block)):
            q_parity[j] = F.Add(q_parity[j], F.Multiply(block[j], factor))
    return bytes(q_parity)


def field_pow(base, exp):
    """
    在有限域中计算幂。
    """
    result = 1
    for _ in range(exp):
        result = F.Multiply(result, base)
    return result


def reconstruct_stripe(data_blocks, p_parity, q_parity, missing_indices):
    """
    重建 RAID-6 条带中丢失的数据块。
    """
    if len(missing_indices) > 2:
        raise ValueError("无法恢复：丢失的块超过两个")

    block_size = len(p_parity)  # 假设所有块大小相同
    data_blocks = [block if block is not None else bytearray(block_size) for block in data_blocks]

    if len(missing_indices) == 0:
        return data_blocks

    if len(missing_indices) == 1:
        # 使用 P 奇偶校验恢复单个丢失的块
        missing_index = missing_indices[0]
        reconstructed_block = bytearray(p_parity)
        for i, block in enumerate(data_blocks):
            if i != missing_index:
                for j in range(block_size):
                    reconstructed_block[j] ^= block[j]
        data_blocks[missing_index] = bytes(reconstructed_block)
        return data_blocks

    # 处理两个丢失块的情况
    m1, m2 = missing_indices

    # 计算 P' 和 Q'
    p_prime = bytearray(p_parity)
    q_prime = bytearray(q_parity)
    for i, block in enumerate(data_blocks):
        if i not in missing_indices:
            for j in range(block_size):
                p_prime[j] ^= block[j]
                q_prime[j] ^= F.Multiply(block[j], field_pow(2, i))

    # 解方程重建丢失的块
    for j in range(block_size):
        a = F.Subtract(field_pow(2, m2), field_pow(2, m1))
        b = F.Subtract(q_prime[j], F.Multiply(p_prime[j], field_pow(2, m2)))

        if a == 0:
            raise ValueError("无法求解：系数为零")

        x = F.Divide(b, a)
        y = F.Add(x, p_prime[j])

        data_blocks[m1] = data_blocks[m1] or bytearray(block_size)
        data_blocks[m2] = data_blocks[m2] or bytearray(block_size)
        data_blocks[m1][j] = x
        data_blocks[m2][j] = y

    return data_blocks


def raid6_stripe(data_blocks):
    """
    为给定的数据块生成 RAID-6 校验。
    """
    block_size = len(data_blocks[0])
    p_parity = bytearray(block_size)
    q_parity = bytearray(block_size)

    for i, block in enumerate(data_blocks):
        for j in range(block_size):
            p_parity[j] ^= block[j]
            q_parity[j] ^= F.Multiply(block[j], field_pow(2, i))

    return bytes(p_parity), bytes(q_parity)