import asyncio
import httpx
from collections import Counter

counter = Counter()

async def hit(i):
    key = f"user{i}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://localhost:5000/{key}")
        if resp.status_code == 200:
            node = resp.json().get("node", "unknown")
            counter[node] += 1

async def main():
    print("Launching 10,000 async requests... ")

    tasks = [hit(i) for i in range(10000)]
    await asyncio.gather(*tasks)

    for node, count in counter.items():
        print(f"{node}: {count} requests")

if __name__ == "__main__":
    asyncio.run(main())
