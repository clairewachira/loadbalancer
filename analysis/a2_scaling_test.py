import asyncio
import httpx
import json
import subprocess
from collections import Counter

replica_sets = {
    2: ["S4", "S5"],
    3: ["S6"],
    4: ["S7"],
    5: ["S8"],
    6: ["S9"]
}

results = {}

# 🔧 Cleanup conflicting containers
def cleanup_old_replicas():
    old_names = ["S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11"]
    for name in old_names:
        subprocess.run(["docker", "rm", "-f", name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

async def hit(i):
    key = f"user{i}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"http://localhost:5000/{key}")
            if resp.status_code == 200:
                return resp.json().get("node", "unknown")
        except:
            return "failed"
    return "failed"

async def run_test(n):
    print(f"\n🧪 Testing with N = {n} replicas")

    tasks = [hit(i) for i in range(10000)]
    responses = await asyncio.gather(*tasks)

    counter = Counter(responses)
    for node, count in counter.items():
        print(f"{node}: {count} requests")

    # average requests per server
    num_servers = len(counter)
    average = 10000 / num_servers if num_servers > 0 else 0
    results[n] = round(average, 2)

async def main():
    cleanup_old_replicas()

    # Reset to base 3 servers
    subprocess.run([
        "curl", "-X", "DELETE", "http://localhost:5000/rm",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"n": 10})
    ], shell=True)

    for n in range(2, 7):
        hostnames = []
        for i in range(2, n + 1):
            hostnames += replica_sets.get(i, [])
        if hostnames:
            subprocess.run([
                "curl", "-X", "POST", "http://localhost:5000/add",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"n": len(hostnames), "hostnames": hostnames})
            ], shell=True)

        await asyncio.sleep(4)  # Wait for containers to start
        await run_test(n)
        await asyncio.sleep(2)

    print("\n📊 Average Load per Server:")
    for n, avg in results.items():
        print(f"N = {n} replicas → avg = {avg} req/server")

    # Save for plotting
    with open("a2_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
