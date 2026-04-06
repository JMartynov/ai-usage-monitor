import pytest
import httpx
import respx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app as main_app
from app.database import Base, get_db
from app.models import RequestLog

# Test Database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

main_app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    main_app.dependency_overrides[get_db] = override_get_db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
@respx.mock
async def test_successful_proxy():
    # 1. Mock upstream (OpenAI)
    mock_url = "https://api.openai.com/v1/chat/completions"
    mock_response_json = {
        "choices": [{"message": {"content": "Hello"}}],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 7,
            "total_tokens": 12
        }
    }
    mock_route = respx.post(mock_url).mock(
        return_value=httpx.Response(
            200, json=mock_response_json))

    # 2. Send request to proxy
    transport = httpx.ASGITransport(app=main_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 0.7
    }
    headers = {
        "Authorization": "Bearer test-key"
    }

    response = await client.post(
        "/v1/chat/completions", json=payload, headers=headers)

    # Verify response passthrough
    assert response.status_code == 200
    assert response.json() == mock_response_json

    # 3. Verify forwarding
    assert mock_route.called
    upstream_request = mock_route.calls.last.request
    assert upstream_request.url == mock_url
    assert upstream_request.headers.get("Authorization") == "Bearer test-key"
    assert "temperature" in httpx.Request(
        upstream_request.method,
        upstream_request.url,
        content=upstream_request.content).content.decode()

    # 4. Verify database
    async with TestingSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(RequestLog))
        logs = result.scalars().all()

        assert len(logs) == 1
        log = logs[0]
        assert log.model == "gpt-3.5-turbo"
        assert log.prompt_tokens == 5
        assert log.completion_tokens == 7
        assert log.total_tokens == 12
        assert "Hi" in log.prompt
        assert log.latency_ms is not None
        assert log.response is not None
        assert log.error is None


@pytest.mark.asyncio
@respx.mock
async def test_upstream_error():
    mock_url = "https://api.openai.com/v1/chat/completions"
    respx.post(mock_url).mock(
        return_value=httpx.Response(
            400, json={
                "error": "bad request"}))

    transport = httpx.ASGITransport(app=main_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    payload = {"model": "gpt-3.5-turbo", "messages": []}

    response = await client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 400
    assert response.json() == {"error": "bad request"}

    async with TestingSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(RequestLog))
        logs = result.scalars().all()
        # Find the log for this specific test
        log = [log_item for log_item in logs
               if log_item.error == "Upstream error 400"][0]

        assert log.error == "Upstream error 400"
        assert log.response is None
        assert log.prompt_tokens is None


@pytest.mark.asyncio
@respx.mock
async def test_timeout_error():
    mock_url = "https://api.openai.com/v1/chat/completions"
    respx.post(mock_url).mock(side_effect=httpx.TimeoutException("Timeout"))

    transport = httpx.ASGITransport(app=main_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    payload = {"model": "gpt-3.5-turbo", "messages": []}

    response = await client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 502
    assert "error" in response.json()
    assert "Timeout" in response.json()["error"]

    async with TestingSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(RequestLog))
        logs = result.scalars().all()
        log = [log_item for log_item in logs
               if "Timeout" in (log_item.error or "")][0]

        assert "Timeout" in log.error
        assert log.response is None
        assert log.prompt_tokens is None


@pytest.mark.asyncio
@respx.mock
async def test_missing_usage():
    mock_url = "https://api.openai.com/v1/chat/completions"
    mock_response_json = {
        "choices": [{"message": {"content": "Hello"}}],
    }
    respx.post(mock_url).mock(
        return_value=httpx.Response(
            200, json=mock_response_json))

    transport = httpx.ASGITransport(app=main_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    payload = {"model": "gpt-3.5-turbo",
               "messages": [{"role": "user", "content": "Hi"}]}

    response = await client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 200
    assert response.json() == mock_response_json

    async with TestingSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(RequestLog))
        logs = result.scalars().all()
        # Find the log with no usage and no error
        log = [log_item for log_item in logs
               if log_item.prompt_tokens is None and log_item.error is None][0]

        assert log.error is None
        assert log.response is not None
        assert log.prompt_tokens is None
        assert log.completion_tokens is None
        assert log.total_tokens is None


@pytest.mark.asyncio
@respx.mock
async def test_header_filtering():
    mock_url = "https://api.openai.com/v1/chat/completions"
    mock_response_json = {
        "choices": [{"message": {"content": "Hello"}}],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 7,
            "total_tokens": 12
        }
    }
    mock_route = respx.post(mock_url).mock(
        return_value=httpx.Response(
            200, json=mock_response_json))

    transport = httpx.ASGITransport(app=main_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    payload = {"model": "gpt-3.5-turbo",
               "messages": [{"role": "user", "content": "Hi"}]}
    headers = {
        "Authorization": "Bearer test-key",
        "Host": "localhost:8000",
        "Content-Length": "100",
        "X-Custom": "Value"
    }

    response = await client.post(
        "/v1/chat/completions", json=payload, headers=headers)
    assert response.status_code == 200

    assert mock_route.called
    upstream_request = mock_route.calls.last.request
    sent_headers = dict(upstream_request.headers)

    assert sent_headers.get("authorization") == "Bearer test-key"
    assert "x-custom" in sent_headers
    # Host and Content-Length might be re-added by httpx,
    # but our proxy shouldn't pass the original ones directly.
    # The proxy removes "host", "content-length",
    # "connection", "accept-encoding".
    # X-Custom should be forwarded.
