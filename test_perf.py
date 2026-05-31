import time
import asyncio
import httpx

async def test_httpx():
    start = time.time()
    for _ in range(100):
        async with httpx.AsyncClient() as client:
            pass
    end = time.time()
    print(f"Time to create 100 AsyncClients: {end - start:.4f} seconds")

asyncio.run(test_httpx())
