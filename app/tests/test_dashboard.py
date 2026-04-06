import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from fastapi import FastAPI
from app.main import app as main_app
from app.database import Base, get_db
from app.models import RequestLog
import datetime

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

app = FastAPI()
for route in main_app.routes:
    app.routes.append(route)

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Populate DB with test data
    async with TestingSessionLocal() as session:
        logs = [
            RequestLog(
                model="gpt-4o",
                prompt="test prompt 1",
                prompt_tokens=10,
                completion_tokens=20,
                total_tokens=30,
                estimated_cost=0.001,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            ),
            RequestLog(
                model="gpt-4o-mini",
                prompt="test prompt 2",
                prompt_tokens=5,
                completion_tokens=10,
                total_tokens=15,
                estimated_cost=0.0005,
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
        ]
        session.add_all(logs)
        await session.commit()

    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_dashboard_ui():
    main_app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=main_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")

    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "AI Usage Dashboard" in response.text


@pytest.mark.asyncio
async def test_dashboard_api_stats():
    main_app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=main_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")

    response = await client.get("/api/stats")
    assert response.status_code == 200

    data = response.json()
    assert "total" in data
    assert data["total"]["requests"] == 2
    assert data["total"]["tokens"] == 45
    assert data["total"]["cost"] == 0.0015

    assert "model_distribution" in data
    assert len(data["model_distribution"]) == 2
    models = [m["model"] for m in data["model_distribution"]]
    assert "gpt-4o" in models
    assert "gpt-4o-mini" in models

    assert "token_breakdown" in data
    assert data["token_breakdown"]["input"] == 15
    assert data["token_breakdown"]["output"] == 30

    assert "recent_activity" in data
    assert len(data["recent_activity"]) == 2
