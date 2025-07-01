# Customizable Load Balancer - Distributed Systems Project
Project Overview
This project implements a scalable and fault-tolerant load balancer using consistent hashing to evenly distribute requests among multiple server replicas. It supports real-time scaling (via /add and /rm) and auto-recovery from failures.

Key Features
Consistent Hashing (512 slots, 9 virtual nodes per server)
Fault-tolerant and dynamic container management via Docker
RESTful API with endpoints: /rep, /add, /rm, /{key}
Performance testing (10,000 async requests) and analysis charts

 Repository Structure
 load-balancer-project/
├── server/
│   ├── Dockerfile
│   ├── server.py
│   └── requirements.txt
│
├── load_balancer/
│   ├── Dockerfile
│   ├── load_balancer.py
│   └── requirements.txt
│
├── analysis/
│   ├── test_load.py
│   ├── a2_scaling_test.py
│  
├── docker-compose.yml
├── Makefile
└── README.md

Installation Instructions
   Prerequisites
Docker Desktop (Windows/Linux/Mac)
Python 3.9+
httpx, matplotlib, asyncio

   Clone and Run
git clone https://github.com/clairewachira/loadbalancer.git
cd load-balancer-project
docker-compose up --build -d

Usage Guidelines
Core API Endpoints

Endpoint    Method        Description
/rep        GET       Lists active replicas
/add        POST      Adds new server containers
/rm         DELETE    Removes server containers
/{key}      GET       Routes request to appropriate server

Example Requests
curl http://localhost:5000/rep
curl http://localhost:5000/home

Testing
  Performance Test Scripts
    Inside /analysis/test_load.py:
    cd analysis
    python test_load.py

  Performance Test Scripts
    Inside /analysis/a2_scaling_test.py:
    cd analysis
    python a2_scaling_test.py

Deployment Instructions
Use Makefile for quick setup:
make build   # Builds Docker images
make up      # Launches all containers
make down    # Stops and removes containers
Ensure Docker is running and no conflicting ports (5000, 8000–8002) are in use.

Additional Materials

Task A-1
![image](https://github.com/user-attachments/assets/4ede1512-1ef1-4461-a1e4-fb84c4c41968)

Task A-2

![image](https://github.com/user-attachments/assets/32651b21-379f-41fd-b752-5bbfd45888df)

Task A-3

![image](https://github.com/user-attachments/assets/d76241d0-78be-4108-84ab-eddc139c90f6)

Task A-4

![image](https://github.com/user-attachments/assets/a1b2c537-0701-4f4f-b312-735a048d7c0e)

![image](https://github.com/user-attachments/assets/f8c4147b-b49b-488e-9284-0bdc69a67cab)







