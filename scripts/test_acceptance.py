import asyncio
import os
import sqlite3
import subprocess
import time
import httpx
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import signal

# --- Mock Upstream Server ---
mock_app = FastAPI()

@mock_app.post("/v1/chat/completions")
async def mock_completions(request: dict):
    model = request.get("model", "unknown")
    if model == "error-model":
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

    # Simple logic to simulate token usage
    prompt = request.get("messages", [{"content": ""}])[0].get("content", "")
    prompt_tokens = len(prompt.split()) * 2
    completion_tokens = 50
    if model == "high-cost-model":
        completion_tokens = 500000

    total_tokens = prompt_tokens + completion_tokens

    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        },
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "This is a mocked response."
            },
            "finish_reason": "stop",
            "index": 0
        }]
    }

def run_mock_server():
    uvicorn.run(mock_app, host="127.0.0.1", port=8001, log_level="error")

# --- Main Acceptance Test ---
def wait_for_server(url, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = httpx.get(url)
            if response.status_code == 200:
                return True
        except httpx.RequestError:
            pass
        time.sleep(0.5)
    return False

async def main():
    db_file = "./test_acceptance.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file}"
    os.environ["OPENAI_API_URL"] = "http://127.0.0.1:8001/v1/chat/completions" # Note: we need to allow configuring this in proxy.py

    print("Starting mock upstream server...")
    mock_process = subprocess.Popen([sys.executable, "-c", "from scripts.test_acceptance import run_mock_server; run_mock_server()"])

    print("Starting main app...")
    app_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "error"])

    try:
        # Wait for both to be up
        if not wait_for_server("http://127.0.0.1:8000/dashboard"):
            print("Main app failed to start.")
            sys.exit(1)

        print("Servers started. Sending traffic...")
        async with httpx.AsyncClient() as client:
            # 1. Normal request
            r = await client.post("http://127.0.0.1:8000/v1/chat/completions", json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hello, world!"}]
            })
            assert r.status_code == 200

            # 2. Another normal request
            r = await client.post("http://127.0.0.1:8000/v1/chat/completions", json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "How are you?"}]
            })
            assert r.status_code == 200

            # 3. High cost request
            r = await client.post("http://127.0.0.1:8000/v1/chat/completions", json={
                "model": "high-cost-model",
                "messages": [{"role": "user", "content": "Write a long book"}]
            })
            assert r.status_code == 200

            # 4. Error request
            r = await client.post("http://127.0.0.1:8000/v1/chat/completions", json={
                "model": "error-model",
                "messages": [{"role": "user", "content": "Fail me"}]
            })
            assert r.status_code == 500

            print("Traffic sent. Validating dashboard stats...")
            # Validate dashboard
            r = await client.get("http://127.0.0.1:8000/api/stats")
            assert r.status_code == 200
            stats = r.json()

            assert stats["total"]["requests"] == 4
            assert stats["total"]["tokens"] > 500000 # Due to high cost request

            print("Validating DB state directly...")
            # Query db directly
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM requests")
            count = cursor.fetchone()[0]
            assert count == 4
            conn.close()

            print("Validating alerts...")
            r = await client.get("http://127.0.0.1:8000/api/alerts")
            assert r.status_code == 200, f"Alerts endpoint failed with status {r.status_code}"
            alerts = r.json()
            # Assuming high-cost triggered an alert
            assert len(alerts) > 0, "No alerts found"
            assert any(a["type"] == "HIGH_COST_REQUEST" for a in alerts), f"No high cost request alert found. Got: {alerts}"

        print("Acceptance tests passed successfully!")

    finally:
        print("Tearing down processes...")
        app_process.terminate()
        mock_process.terminate()
        app_process.wait()
        mock_process.wait()
        if os.path.exists(db_file):
            os.remove(db_file)

if __name__ == "__main__":
    asyncio.run(main())
