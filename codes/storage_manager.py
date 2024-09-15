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

def send_command(host, port, command, data=None):
    response = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(command.encode('utf-8'))
        if data:
            s.sendall(data)
        response = s.recv(1024).decode('utf-8').strip()
    return response

def store_block(node, filename, data):
    host, port = node['host'], node['port']
    command = f'STORE {filename} {len(data)}\n'
    response = send_command(host, port, command, data)
    if response != 'OK':
        print(f'Error storing block {filename} on {node["name"]}: {response}')

def retrieve_block(node, filename):
    host, port = node['host'], node['port']
    command = f'RETRIEVE {filename}\n'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(command.encode('utf-8'))
        response = s.recv(1024).decode('utf-8').strip()
        if response.startswith('OK'):
            _, filesize = response.split()
            filesize = int(filesize)
            data = b''
            while len(data) < filesize:
                packet = s.recv(4096)
                if not packet:
                    break
                data += packet
            return data
        else:
            print(f'Error retrieving block {filename} from {node["name"]}: {response}')
            return None
