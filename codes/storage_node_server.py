# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# @File     : storage_node_server.py
# @Project  : raid6
# Time      : 14/9/24 4:28 pm
# Author    : honywen
# version   : python 3.8
# Description：
"""



# storage_node_server.py

import socket
import threading
import os

STORAGE_DIR = 'storage'

def handle_client(conn, addr):
    try:
        while True:
            command = conn.recv(1024).decode('utf-8').strip()
            if not command:
                break
            if command.startswith('STORE'):
                _, filename, filesize = command.split()
                filesize = int(filesize)
                data = b''
                while len(data) < filesize:
                    packet = conn.recv(4096)
                    if not packet:
                        break
                    data += packet
                if not os.path.exists(STORAGE_DIR):
                    os.makedirs(STORAGE_DIR)
                with open(os.path.join(STORAGE_DIR, filename), 'wb') as f:
                    f.write(data)
                conn.sendall(b'OK\n')
            elif command.startswith('RETRIEVE'):
                _, filename = command.split()
                filepath = os.path.join(STORAGE_DIR, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        data = f.read()
                    conn.sendall(f'OK {len(data)}\n'.encode('utf-8'))
                    conn.sendall(data)
                else:
                    conn.sendall(b'ERROR File not found\n')
            elif command.startswith('DELETE'):
                _, filename = command.split()
                filepath = os.path.join(STORAGE_DIR, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    conn.sendall(b'OK\n')
                else:
                    conn.sendall(b'ERROR File not found\n')
            else:
                conn.sendall(b'ERROR Unknown command\n')
    finally:
        conn.close()

def start_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(5)
    print(f'Storage node server started on port {port}')
    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    finally:
        server_socket.close()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    start_server(port)