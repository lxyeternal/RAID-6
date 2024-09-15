# RAID-6 Distributed Storage System

## Overview

This project is a simulation of a RAID-6 distributed storage system implemented in Python, utilizing Docker containers to simulate individual storage nodes (disks). The system allows for customizable data chunk sizes and can handle arbitrary files of any size and format. It demonstrates the principles of RAID-6, including data striping and parity calculations, to provide fault tolerance against disk failures.

---

## Table of Contents

- [Project Description](#project-description)
- [RAID-6 Principles](#raid-6-principles)
- [Project Structure](#project-structure)
  - [Files and Directories](#files-and-directories)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Build the Docker Image](#2-build-the-docker-image)
  - [3. Start Storage Nodes Using Docker Compose](#3-start-storage-nodes-using-docker-compose)
- [Running the System](#running-the-system)
  - [1. Run the Main Program](#1-run-the-main-program)
  - [2. Simulate Failures](#2-simulate-failures)
  - [3. Data Reconstruction](#3-data-reconstruction)
  - [4. Verify Data Integrity](#4-verify-data-integrity)
- [Testing and Usage](#testing-and-usage)
- [Cleaning Up](#cleaning-up)
- [Project Details](#project-details)
  - [Storage Node Server](#storage-node-server)
  - [RAID-6 Implementation](#raid-6-implementation)
- [Additional Information](#additional-information)
- [Contributing](#contributing)
- [License](#license)

---

## Project Description

The project simulates a RAID-6 storage system using Python and Docker. It demonstrates how data can be distributed across multiple storage nodes with fault tolerance, allowing the system to recover from up to two simultaneous disk failures per stripe. The system supports customizable data chunk sizes (e.g., in KB or MB) and can handle arbitrary files of any size and format.

---

## RAID-6 Principles

RAID-6 combines data striping with dual parity blocks to provide fault tolerance. The key concepts include:

- **Data Striping**: Dividing data into blocks (chunks) and distributing them across multiple disks.
- **Parity Calculations**: Generating parity information (P and Q parity) to allow reconstruction of lost data.
  - **P Parity**: XOR of all data blocks in a stripe (similar to RAID-5).
  - **Q Parity**: Reed-Solomon coding over Galois Field GF(2^8) for the second parity.
- **Fault Tolerance**: Ability to recover from the failure of up to two disks in any stripe.

---

## Project Structure

### Files and Directories

- **`main.py`**: The main program that orchestrates file storage, retrieval, and reconstruction.
- **`raid6.py`**: Contains functions for RAID-6 parity calculations and data reconstruction.
- **`storage_manager.py`**: Manages communication between the main program and storage nodes.
- **`utilities.py`**: Utility functions for file reading, writing, and directory management.
- **`storage_node/`**: Directory containing files related to the storage node server.
  - **`storage_node_server.py`**: The server script that runs on each storage node (Docker container).
  - **`Dockerfile`**: Dockerfile to build the storage node Docker image.
- **`docker-compose.yml`**: Docker Compose configuration file to manage storage node containers.
- **`start_storage_nodes.sh`**: Shell script to start all storage node containers individually.
- **`stop_storage_nodes.sh`**: Shell script to stop and remove all storage node containers.
- **`README.md`**: Project documentation.
- **`LICENSE`**: Project license information.


---

## Prerequisites

- **Python 3.7+**: Ensure Python is installed on your system.
- **Docker**: Install Docker to run storage node containers.
- **Docker Compose**: Install Docker Compose to manage multiple containers.
- **Python Packages**:
  - `pyfinite`: For Galois Field arithmetic in RAID-6 calculations.
  - Install dependencies using:

    ```bash
    pip install pyfinite
    ```

---

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your_username/raid6_project.git
cd raid6_project
```
### 2. Build the Docker Image
Navigate to the storage_node/ directory and build the Docker image:

```bash
cd storage_node/
docker build -t storage_node .
```
This command builds a Docker image named storage_node using the Dockerfile.


### 3. Set Execute Permissions on Shell Scripts
Return to the project root directory and set execute permissions on the shell scripts:

```bash
cd ..
chmod +x start_storage_nodes.sh stop_storage_nodes.sh
```
start_storage_nodes.sh: Script to start all storage node containers.
stop_storage_nodes.sh: Script to stop and remove all storage node containers.


### 4. Start Storage Nodes
You have two options to start the storage nodes:

#### Option 1: Using Docker Compose
Start the storage node containers using Docker Compose:

```bash
docker-compose up -d
```
This command starts eight containers (node1 to node6, parity1, and parity2) as defined in docker-compose.yml.
Each container simulates a disk in the RAID-6 array.

#### Option 2: Using Shell Script
Alternatively, you can start the storage nodes using the provided shell script:

```bash
./start_storage_nodes.sh
```
This script runs docker run commands to start each container individually.
Ensure that start_storage_nodes.sh has execute permissions (chmod +x start_storage_nodes.sh).


## Running the System
### 1. Run the Main Program

Execute the main program:
```bash
python main.py
```
Input File: When prompted, enter the path to the file you wish to store (e.g., /path/to/file.txt).
Block Size: Specify the data chunk size (e.g., 1KB, 4MB).

### Example:
```Bash
Enter the path to the input file: /path/to/test.zip
Enter the block size (e.g., 1KB, 4MB): 1MB
```
###  2. Simulate Failures
Choose to simulate disk failures or data block corruption:

Disk Failure:
Enter 'A' when prompted.
Input the indices of the disks to fail (e.g., 1 3 for node2 and node4).

Example:
```Bash
Choose failure type:
A: Simulate disk failure (enter indices 0-7 for disks or parity)
B: Simulate data block corruption (enter block IDs)
Enter 'A' for disk failure or 'B' for data block corruption: A
Enter the indices of up to two failed disks separated by spaces (e.g., 0 6): 1 3
Failed disks: ['node2', 'node4']
```
Data Block Corruption:
Enter 'B' when prompted.
Input the block IDs to corrupt.


### 3. Data Reconstruction
The program will attempt to reconstruct missing or corrupted data blocks using parity information. It will display messages indicating which blocks were reconstructed.

### 4. Verify Data Integrity
The restored file will be saved with the prefix restored_ (e.g., restored_test.zip). Verify that the restored file matches the original file:

Compare file sizes.
Calculate checksums (e.g., MD5, SHA256).
Attempt to open or use the restored file.

## Testing and Usage
Store a File: Run main.py and follow the prompts to store your desired file across the storage nodes. <br>
Simulate Failures: Choose to simulate disk failures or data corruption to test the fault tolerance of the system. <br>
Retrieve and Reconstruct: The system will automatically attempt to retrieve and reconstruct the original file. <br>
Validate Results: Ensure that the restored file is identical to the original. <br>

## Cleaning Up
To stop and remove the Docker containers, use the following command:

```bash
docker-compose down
```