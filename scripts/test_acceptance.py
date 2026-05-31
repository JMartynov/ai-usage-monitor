import os
import sqlite3
import subprocess
import time
import httpx
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import pytest
import pytest_asyncio


# --- Mock Upstream Server ---
mock_app = FastAPI()


@mock_app.post("/v1/chat/completions")
async def mock_completions(request: dict):
    model = request.get("model", "unknown")
    if model == "error-model":
        return JSONResponse(
            status_code=500, content={"error": "Internal Server Error"}
        )

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


# --- Pytest Fixtures ---
DB_FILE = "./test_acceptance.db"


@pytest.fixture(scope="module")
def setup_test_environment():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_FILE}"
    os.environ["OPENAI_API_URL"] = "http://127.0.0.1:8001/v1/chat/completions"

    mock_process = subprocess.Popen([
        sys.executable,
        "-c",
        "from scripts.test_acceptance import run_mock_server; "
        "run_mock_server()"
    ])
    app_process = subprocess.Popen([
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--log-level",
        "error"
    ])

    if not wait_for_server("http://127.0.0.1:8000/dashboard"):
        app_process.terminate()
        mock_process.terminate()
        raise RuntimeError("Main app failed to start.")

    yield

    app_process.terminate()
    mock_process.terminate()
    app_process.wait()
    mock_process.wait()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


@pytest_asyncio.fixture(scope="function")
async def async_client(setup_test_environment):
    async with httpx.AsyncClient() as client:
        yield client


# --- Acceptance Tests ---

# We use order markers implicitly by just having them run sequentially
# since they share the database state.
# Pytest runs tests in the order they are defined.

@pytest.mark.asyncio
async def test_normal_request(async_client):
    r = await async_client.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello, world!"}]
        }
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_another_normal_request(async_client):
    r = await async_client.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "How are you?"}]
        }
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_high_cost_request(async_client):
    r = await async_client.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        json={
            "model": "high-cost-model",
            "messages": [{"role": "user", "content": "Write a long book"}]
        }
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_error_request(async_client):
    r = await async_client.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        json={
            "model": "error-model",
            "messages": [{"role": "user", "content": "Fail me"}]
        }
    )
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_dashboard_stats(async_client):
    r = await async_client.get("http://127.0.0.1:8000/api/stats")
    assert r.status_code == 200
    stats = r.json()

    assert stats["total"]["requests"] == 4
    assert stats["total"]["tokens"] > 500000


@pytest.mark.asyncio
async def test_db_state_directly(setup_test_environment):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM requests")
    count = cursor.fetchone()[0]
    assert count == 4
    conn.close()


@pytest.mark.asyncio
async def test_alerts_endpoint(async_client):
    r = await async_client.get("http://127.0.0.1:8000/api/alerts")
    assert r.status_code == 200, (
        f"Alerts endpoint failed with status {r.status_code}"
    )
    alerts = r.json()
    assert len(alerts) > 0, "No alerts found"
    assert any(
        a["type"] == "cost" or a["type"] == "budget" for a in alerts
    ), "No cost or budget alert found"
