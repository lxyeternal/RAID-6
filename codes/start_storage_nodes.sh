#!/bin/bash

docker run -d --name node1 -p 5001:5000 storage_node
docker run -d --name node2 -p 5002:5000 storage_node
docker run -d --name node3 -p 5003:5000 storage_node
docker run -d --name node4 -p 5004:5000 storage_node
docker run -d --name node5 -p 5005:5000 storage_node
docker run -d --name node6 -p 5006:5000 storage_node
docker run -d --name parity1 -p 5007:5000 storage_node
docker run -d --name parity2 -p 5008:5000 storage_node