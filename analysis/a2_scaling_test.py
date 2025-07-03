import asyncio
import httpx
import json
from collections import Counter

replica_sets = {
    2: ["server1", "server2"],
    3: ["server3"],
    4: ["server4"],
    5: ["server5"],
    6: ["server6"]
}

results = {}

async def hit(i):
    key = f"user{i}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:5000/{key}")
            if resp.status_code == 200:
                return resp.json().get("node", "unknown")
            return f"http_{resp.status_code}"
        except Exception as e:
            return f"failed: {str(e)}"

async def run_test(n):
    print(f"\n Testing with N = {n} replicas")
    
    async with httpx.AsyncClient() as client:
        try:
            rep_resp = await client.get("http://127.0.0.1:5000/rep")
            print("Current replicas:", rep_resp.json().get("nodes", []))
        except Exception as e:
            print(f"Failed to get replicas: {e}")
            return

    tasks = [hit(i) for i in range(100)]
    responses = await asyncio.gather(*tasks)

    counter = Counter(responses)
    print("\n Distribution:")
    for node, count in counter.items():
        print(f"{node}: {count} requests")

    successful = sum(count for node, count in counter.items() if "failed" not in node)
    if successful > 0:
        avg = successful / len([n for n in counter if "failed" not in n])
        results[n] = round(avg, 2)
        print(f"Average: {results[n]} requests per server")
    else:
        results[n] = 0
        print("All requests failed!")

async def main():
    print(" Resetting to initial state...")
    async with httpx.AsyncClient() as client:
        try:
            await client.request(
                "DELETE",
                "http://127.0.0.1:5000/rm",
                json={"n": 10},
                timeout=10.0
            )
        except Exception as e:
            print(f"Reset failed: {e}")
            return

    for n in range(2, 7):
        print(f"\n Setting up N = {n} replicas")
        hostnames = replica_sets.get(n, [])
        
        if hostnames:
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(
                        "http://127.0.0.1:5000/add",
                        json={"n": len(hostnames), "hostnames": hostnames},
                        timeout=10.0
                    )
                except Exception as e:
                    print(f"Failed to add replicas: {e}")
                    continue
        
        await asyncio.sleep(3)
        await run_test(n)
        await asyncio.sleep(1)

    print("\n Final Results:")
    for n, avg in results.items():
        print(f"N = {n} replicas → avg = {avg} req/server")

    with open("a2_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
