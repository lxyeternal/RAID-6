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



# storage_manager.py

import socket


def check_node_online(node):
    try:
        with socket.create_connection((node['host'], node['port']), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def send_command(host, port, command, data=None):
    response = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(command.encode('utf-8'))
        if data:
            s.sendall(data)
        response_line = ''
        while not response_line.endswith('\n'):
            chunk = s.recv(1).decode('utf-8')
            if not chunk:
                break
            response_line += chunk
        response = response_line.strip()
    return response

def store_block(node, filename, data):
    host, port = node['host'], node['port']
    command = f'STORE {filename} {len(data)}\n'
    try:
        response = send_command(host, port, command, data)
        if response != 'OK':
            print(f'Error storing block {filename} on {node["name"]}: {response}')
        else:
            print(f'Successfully stored block {filename} on {node["name"]}')
    except Exception as e:
        print(f'Failed to store block {filename} on {node["name"]}: {str(e)}')

def retrieve_block(node, filename):
    host, port = node['host'], node['port']
    command = f'RETRIEVE {filename}\n'
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(command.encode('utf-8'))
            response_line = ''
            while not response_line.endswith('\n'):
                chunk = s.recv(1).decode('utf-8')
                if not chunk:
                    break
                response_line += chunk
            response = response_line.strip()
            if response.startswith('OK'):
                _, filesize_str = response.split()
                filesize = int(filesize_str)
                data = b''
                while len(data) < filesize:
                    packet = s.recv(min(filesize - len(data), 4096))
                    if not packet:
                        break
                    data += packet
                print(f'Successfully retrieved block {filename} from {node["name"]}')
                return data
            else:
                print(f'Error retrieving block {filename} from {node["name"]}: {response}')
                return None
    except Exception as e:
        print(f'Failed to retrieve block {filename} from {node["name"]}: {str(e)}')
        return None