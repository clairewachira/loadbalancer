import asyncio
import uuid
import httpx
from collections import Counter

counter = Counter()
TIMEOUT = 10.0  # Increased timeout

async def hit(i):
    key = str(uuid.uuid4())
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"http://127.0.0.1:5000/{key}")
            if resp.status_code == 200:
                node = resp.json().get("node", "unknown")
                counter[node] += 1
            else:
                counter[f"HTTP_{resp.status_code}"] += 1
        except httpx.ConnectError:
            counter["ConnectionFailed"] += 1
        except httpx.TimeoutException:
            counter["Timeout"] += 1
        except Exception as e:
            counter[f"Error_{type(e).__name__}"] += 1

async def main():
    # Verify LB health first
    try:
        async with httpx.AsyncClient() as client:
            health = await client.get("http://127.0.0.1:5000/rep", timeout=5.0)
            print("Load Balancer Status:", health.json())
    except Exception as e:
        print(f" Load Balancer Unavailable: {e}")
        return

    # Run test
    print(f"Testing with {TIMEOUT}s timeout...")
    tasks = [hit(i) for i in range(100)]  # Start with 100 requests
    await asyncio.gather(*tasks)

    # Results
    print("\nResults:")
    for node, count in counter.most_common():
        print(f"{node}: {count}")

if __name__ == "__main__":
    asyncio.run(main())
