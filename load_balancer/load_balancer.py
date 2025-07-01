from fastapi import FastAPI, Request
import httpx
import hashlib
import bisect
import docker
import random
import asyncio
import uuid 


app = FastAPI()

# Constants 
M = 512  # Total number of slots in the hash ring
K = 9    # Number of virtual nodes per server

# Docker client to manage containers
client = docker.from_env()


class ConsistentHashRing:
    def __init__(self, nodes=None):
        self.ring = {}           # slot -> node
        self.sorted_slots = []   # sorted list of slots
        if nodes:
            for idx, node in enumerate(nodes):
                self.add_physical_node(idx, node)

    # Hash function H(i) =i^2 + 31i + 101 new formula
    def hash_request(self, key: str):
        i = sum(ord(c) for c in key)
        return (i * i + 31 * i + 101) % M 

    # Φ(i, j) =  (i+1)^2 + (j+3)^2 + 19 new formula
    def hash_virtual(self, i: int, j: int):
        return ((i + 1)**2 + (j + 3)**2 + 19) % M 

    def add_physical_node(self, server_id, node):
        for j in range(K):
            slot = self.hash_virtual(server_id, j)
            while slot in self.ring:
                slot = (slot + 1) % M
            self.ring[slot] = node
            bisect.insort(self.sorted_slots, slot)

    def remove_physical_node(self, node):
        to_remove = []
        for slot, server in self.ring.items():
            if server == node:
                to_remove.append(slot)
        for slot in to_remove:
            del self.ring[slot]
            self.sorted_slots.remove(slot)

    def get_node(self, key: str):
        if not self.ring:
            return None
        hashed_slot = self.hash_request(key)
        idx = bisect.bisect(self.sorted_slots, hashed_slot) % len(self.sorted_slots)
        return self.ring[self.sorted_slots[idx]]


# Initial backend servers — match docker-compose service names
nodes = [
    "http://server1:8000",
    "http://server2:8000",
    "http://server3:8000"
]

hash_ring = ConsistentHashRing(nodes)


@app.get("/rep")
async def get_replica():
    return {
        "message": "Load Balancer up and running!",
        "nodes": nodes
    }


@app.get("/{key}")
async def route_request(key: str):
    node = hash_ring.get_node(key)
    if node is None:
        return {"error": "No backend available"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{node}/{key}")
            return {"node": node, "response": response.json()}
    except httpx.RequestError as e:
        return {"error": f"Could not reach backend node: {node}", "details": str(e)}


@app.post("/add")
async def add_servers(request: Request):
    payload = await request.json()
    n = payload.get("n")
    hostnames = payload.get("hostnames", [])

    if not isinstance(n, int) or n <= 0:
        return {"error": "Invalid 'n'. Must be a positive integer."}

    if len(hostnames) > n:
        return {
            "error": "Length of hostname list exceeds number of instances to add.",
            "status": "failure"
        }

    image = "myservers"  # Match your actual image name
    created = []

    for i in range(n):
        name = hostnames[i] if i < len(hostnames) else f"dyn_server_{len(nodes)+i}"
        try:
            container = client.containers.run(
                image=image,
                name=name,
                network="load-balancer-project_net1",
                detach=True,
                ports={},  # Not exposed to host
                environment={"SERVER_ID": name}
            )
            node_url = f"http://{name}:8000"
            nodes.append(node_url)
            hash_ring.add_physical_node(len(nodes), node_url)
            created.append(name)
        except docker.errors.APIError as e:
            return {
                "error": f"Failed to start container {name}: {str(e)}",
                "status": "failure"
            }

    # Build response as required
    all_hostnames = [url.replace("http://", "").split(":")[0] for url in nodes]

    return {
        "message": {
            "N": len(nodes),
            "replicas": all_hostnames
        },
        "status": "successful"
    }


@app.delete("/rm")
async def remove_servers(request: Request):
    payload = await request.json()
    n = payload.get("n")
    hostnames = payload.get("hostnames", [])

    if not isinstance(n, int) or n <= 0:
        return {"error": "Invalid 'n'. Must be a positive integer.", "status": "failure"}

    if len(hostnames) > n:
        return {
            "error": "Length of hostname list is more than removable instances",
            "status": "failure"
        }

    all_hostnames = [url.replace("http://", "").split(":")[0] for url in nodes]

    to_remove = []
    used = set()

    # 1. Add preferred hostnames (if they exist)
    for name in hostnames:
        if name in all_hostnames and name not in used:
            to_remove.append(name)
            used.add(name)

    # 2. Randomly choose more if needed
    candidates = list(set(all_hostnames) - used)
    random.shuffle(candidates)
    while len(to_remove) < n and candidates:
        name = candidates.pop()
        to_remove.append(name)

    # 3. Remove containers and update structures
    for name in to_remove:
        try:
            container = client.containers.get(name)
            container.stop()
            container.remove()
        except docker.errors.NotFound:
            continue

        node_url = f"http://{name}:8000"
        if node_url in nodes:
            nodes.remove(node_url)
            hash_ring.remove_physical_node(node_url)

    # 4. Final output (assignment format)
    updated = [url.replace("http://", "").split(":")[0] for url in nodes]

    return {
        "message": {
            "N": len(nodes),
            "replicas": updated
        },
        "status": "successful"
    }


@app.on_event("startup")
async def monitor_replicas():
    async def monitor():
        while True:
            dead = []
            for node in list(set(hash_ring.ring.values())):
                try:
                    async with httpx.AsyncClient(timeout=2.0) as hc:
                        await hc.get(f"{node}/heartbeat")
                except:
                    dead.append(node)

            for node in dead:
                name = node.split("//")[1].split(":")[0]
                print(f"⚠️ Server down: {name}, replacing...")

                # Remove from system
                hash_ring.remove_physical_node(node)
                if node in nodes:
                    nodes.remove(node)

                try:
                    container = client.containers.get(name)
                    container.remove(force=True)
                except:
                    pass

                # Spawn replacement
                new_name = f"dyn_server_{uuid.uuid4().hex[:6]}"
                new_node = f"http://{new_name}:8000"
                try:
                    client.containers.run(
                        image="myservers",
                        name=new_name,
                        network="load-balancer-project_net1",
                        detach=True,
                        environment={"SERVER_ID": new_name}
                    )
                    hash_ring.add_physical_node(999, new_node)
                    nodes.append(new_node)
                    print(f"✅ Spawned replacement: {new_name}")
                except Exception as e:
                    print(f"❌ Failed to spawn: {e}")

            await asyncio.sleep(5)

    asyncio.create_task(monitor())