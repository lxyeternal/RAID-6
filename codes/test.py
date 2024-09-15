import os
import shutil
from utilities import read_file_to_blocks, write_blocks_to_file

# RAID-6 配置
DATA_DISKS = 6
PARITY_DISKS = 2
TOTAL_DISKS = DATA_DISKS + PARITY_DISKS
STORAGE_DIR = 'raid6_storage'
DISK_PATHS = [f'disk{i}' for i in range(TOTAL_DISKS)]  # 用文件夹模拟磁盘
METADATA_DISK = DISK_PATHS[0]  # 元数据存储在 disk0


# 初始化磁盘文件夹
def init_disks():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

    for disk in DISK_PATHS:
        disk_path = os.path.join(STORAGE_DIR, disk)
        if not os.path.exists(disk_path):
            os.makedirs(disk_path)


# 存储元数据，保存到磁盘 0
def save_metadata(file_name, block_size, num_blocks):
    metadata = {
        'original_filename': file_name,
        'block_size': block_size,
        'num_blocks': num_blocks
    }
    with open(os.path.join(STORAGE_DIR, METADATA_DISK, 'metadata.txt'), 'w') as f:
        f.write(str(metadata))


# 加载元数据
def load_metadata():
    with open(os.path.join(STORAGE_DIR, METADATA_DISK, 'metadata.txt'), 'r') as f:
        metadata = eval(f.read())  # 用 eval 来解析元数据
    return metadata


# 模拟存储数据到 RAID-6
def store_raid6(blocks, original_size, original_filename, block_size):
    save_metadata(original_filename, block_size, len(blocks))

    # 按条带组织数据块并存储在不同磁盘中
    stripes = []
    for i in range(0, len(blocks), DATA_DISKS):
        stripe_data_blocks = list(blocks[i:i + DATA_DISKS])
        if len(stripe_data_blocks) < DATA_DISKS:
            stripe_data_blocks += [bytes(block_size)] * (DATA_DISKS - len(stripe_data_blocks))

        p_parity, q_parity = raid6_stripe(stripe_data_blocks)
        stripes.append((stripe_data_blocks, p_parity, q_parity))

    # 将条带数据存储到不同磁盘
    for stripe_index, (data_blocks, p_parity, q_parity) in enumerate(stripes):
        for i, block in enumerate(data_blocks):
            store_block(DISK_PATHS[i], f'stripe_{stripe_index}_block_{i}', block)
        store_block(DISK_PATHS[-2], f'stripe_{stripe_index}_parity_p', p_parity)
        store_block(DISK_PATHS[-1], f'stripe_{stripe_index}_parity_q', q_parity)

    print("Data stored to disks successfully.")


# 存储单个数据块到磁盘
def store_block(disk, filename, block):
    disk_path = os.path.join(STORAGE_DIR, disk)
    if not os.path.exists(disk_path):
        os.makedirs(disk_path)
    with open(os.path.join(disk_path, filename), 'wb') as f:
        f.write(block)


# 从磁盘恢复数据块
def retrieve_block(disk, filename):
    file_path = os.path.join(STORAGE_DIR, disk, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return f.read()
    return None


# RAID-6 的条带校验计算 (已修复 Q 校验计算)
def raid6_stripe(data_blocks):
    block_size = len(data_blocks[0])  # 假设所有块大小相同
    p_parity = bytearray(block_size)  # 用 bytearray 可以执行异或操作
    q_parity = bytearray(block_size)

    for i, block in enumerate(data_blocks):
        for j in range(block_size):
            p_parity[j] ^= block[j]  # 将 block[j] 直接作为字节异或运算
            q_parity[j] ^= (block[j] * (i + 1)) % 256  # 确保 Q 校验结果在 0-255 范围内

    return bytes(p_parity), bytes(q_parity)


# 检查缺失的磁盘
def check_missing_disks():
    missing_disks = []
    for disk in DISK_PATHS:
        disk_path = os.path.join(STORAGE_DIR, disk)
        if not os.path.exists(disk_path):
            missing_disks.append(disk)
    return missing_disks


def reconstruct_stripe(data_blocks, p_parity, q_parity, missing_indices):
    block_size = len(p_parity)
    num_missing = len(missing_indices)

    if num_missing == 0:
        return data_blocks

    if num_missing == 1:
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
        print(f"Reconstructed block at index {missing_index}")
        return data_blocks

    if num_missing == 2:
        m1, m2 = missing_indices
        reconstructed_block1 = bytearray(block_size)
        reconstructed_block2 = bytearray(block_size)

        for j in range(block_size):
            p_parity_byte = p_parity[j]
            q_parity_byte = q_parity[j]

            sum_p = p_parity_byte
            sum_q = q_parity_byte

            for i, block in enumerate(data_blocks):
                if i != m1 and i != m2 and block is not None:
                    block_byte = block[j]
                    sum_p ^= block_byte
                    sum_q ^= (block_byte * (i + 1)) % 256

            D_m1 = (sum_q ^ sum_p * (m2 + 1)) // ((m1 + 1) ^ (m2 + 1))
            D_m2 = sum_p ^ D_m1

            reconstructed_block1[j] = D_m1
            reconstructed_block2[j] = D_m2

        data_blocks[m1] = bytes(reconstructed_block1)
        data_blocks[m2] = bytes(reconstructed_block2)

        print(f"Reconstructed blocks at indices {m1} and {m2}")
        return data_blocks


# 恢复数据
def recover_data():
    missing_disks = check_missing_disks()

    if len(missing_disks) > 2:
        print(f"More than 2 disks are missing: {missing_disks}, cannot recover the data.")
        return

    metadata = load_metadata()
    original_file_size = metadata['num_blocks'] * metadata['block_size']
    block_size = metadata['block_size']

    reconstructed_blocks = []
    num_stripes = (metadata['num_blocks'] + DATA_DISKS - 1) // DATA_DISKS  # 向上取整

    for stripe_index in range(num_stripes):
        data_blocks = []
        missing_indices = []

        for i in range(DATA_DISKS):
            block = retrieve_block(DISK_PATHS[i], f'stripe_{stripe_index}_block_{i}')
            if block is None:
                data_blocks.append(None)
                missing_indices.append(i)
            else:
                data_blocks.append(block)

        p_parity = retrieve_block(DISK_PATHS[-2], f'stripe_{stripe_index}_parity_p')
        q_parity = retrieve_block(DISK_PATHS[-1], f'stripe_{stripe_index}_parity_q')

        if len(missing_indices) <= 2:
            reconstructed_data_blocks = reconstruct_stripe(data_blocks, p_parity, q_parity, missing_indices)

            # 将重建的数据块写回到相应的磁盘
            for i, block in enumerate(reconstructed_data_blocks):
                if i in missing_indices:
                    disk_path = os.path.join(STORAGE_DIR, DISK_PATHS[i])
                    if not os.path.exists(disk_path):
                        os.makedirs(disk_path)
                    store_block(DISK_PATHS[i], f'stripe_{stripe_index}_block_{i}', block)
                    print(f"Reconstructed and stored block for disk {i}, stripe {stripe_index}")

            reconstructed_blocks.extend(reconstructed_data_blocks[:DATA_DISKS])

    # 重建 P 和 Q 校验，如果它们在丢失的磁盘中
    if DISK_PATHS[-2] in missing_disks or DISK_PATHS[-1] in missing_disks:
        for stripe_index in range(num_stripes):
            stripe_data = [retrieve_block(DISK_PATHS[i], f'stripe_{stripe_index}_block_{i}') for i in range(DATA_DISKS)]
            p_parity, q_parity = raid6_stripe(stripe_data)

            if DISK_PATHS[-2] in missing_disks:
                store_block(DISK_PATHS[-2], f'stripe_{stripe_index}_parity_p', p_parity)
            if DISK_PATHS[-1] in missing_disks:
                store_block(DISK_PATHS[-1], f'stripe_{stripe_index}_parity_q', q_parity)

    restore_folder = create_restore_folder()
    output_file = os.path.join(restore_folder, 'restored_' + metadata['original_filename'])
    write_blocks_to_file(reconstructed_blocks, output_file, original_file_size)
    print(f"Restored file saved as '{output_file}'.")


def create_restore_folder():
    restore_folder = "restored_files"
    if not os.path.exists(restore_folder):
        os.makedirs(restore_folder)
    return restore_folder


if __name__ == "__main__":
    init_disks()
    choice = input("选择操作：1. 存储文件  2. 恢复数据 ")
    if choice == '1':
        file_path = input("请输入要存储的文件路径: ")
        if not os.path.exists(file_path):
            print("错误：文件不存在")
        else:
            block_size_input = input("请输入块大小 (e.g., 1KB, 4MB): ").strip().upper()
            if block_size_input.endswith('KB'):
                block_size = int(block_size_input[:-2]) * 1024
            elif block_size_input.endswith('MB'):
                block_size = int(block_size_input[:-2]) * 1024 * 1024
            else:
                print("无效的块大小格式")
                exit(1)

            blocks, file_size = read_file_to_blocks(file_path, block_size)
            original_filename = os.path.basename(file_path)
            store_raid6(blocks, os.path.getsize(file_path), original_filename, block_size)
            print(f"文件 '{original_filename}' 已成功存储到 RAID-6 系统中。")
    elif choice == '2':
        recover_data()
    else:
        print("无效的选择")
