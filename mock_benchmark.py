import asyncio
import time
import httpx
from app.main import app
from asgi_lifespan import LifespanManager
import respx

async def run_benchmark(n=500):
    transport = httpx.ASGITransport(app=app)

    mock_url = "https://api.openai.com/v1/chat/completions"
    mock_response_json = {
        "choices": [{"message": {"content": "Hello"}}],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 7,
            "total_tokens": 12
        }
    }

    with respx.mock:
        respx.post(mock_url).mock(
            return_value=httpx.Response(200, json=mock_response_json)
        )
        async with LifespanManager(app):
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "temperature": 0.7
                }

                # warm up
                for _ in range(5):
                    await client.post("/v1/chat/completions", json=payload)

                start = time.time()
                tasks = [client.post("/v1/chat/completions", json=payload) for _ in range(n)]
                await asyncio.gather(*tasks)
                end = time.time()
                print(f"Time for {n} requests: {end - start:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
