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

async def hit(i):
    key = f"user{i}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"http://localhost:5000/{key}")
            if resp.status_code == 200:
                node = resp.json().get("node", "unknown")
                return node
        except Exception:
            return "failed"
    return "failed"

async def run_test(n):
    print(f"\n🧪 Testing with N = {n} replicas")

    tasks = [hit(i) for i in range(10000)]
    responses = await asyncio.gather(*tasks)

    counter = Counter(responses)
    for node, count in counter.items():
        print(f"{node}: {count} requests")

    average = sum(counter.values()) / len(counter)
    results[n] = round(average, 2)

async def main():
    # Reset to base 1-3 servers
    subprocess.run(["curl", "-X", "DELETE", "http://localhost:5000/rm", "-H", "Content-Type: application/json", "-d", json.dumps({"n": 10})])

    for n in range(2, 7):
        hostnames = []
        for i in range(2, n + 1):
            hostnames += replica_sets.get(i, [])
        subprocess.run(["curl", "-X", "POST", "http://localhost:5000/add", "-H", "Content-Type: application/json", "-d", json.dumps({"n": len(hostnames), "hostnames": hostnames})])

        await asyncio.sleep(3)  # Wait for containers to start
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
