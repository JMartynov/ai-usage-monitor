import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import RequestLog
import datetime

from app.routers.dashboard import api_stats

# Setup DB
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert a bunch of records
    async with TestingSessionLocal() as session:
        logs = []
        for i in range(1000):
            logs.append(
                RequestLog(
                    model="gpt-4",
                    prompt=f"test prompt {i}",
                    prompt_tokens=10,
                    completion_tokens=20,
                    total_tokens=30,
                    estimated_cost=0.001,
                    timestamp=datetime.datetime.now(datetime.timezone.utc)
                )
            )
        session.add_all(logs)
        await session.commit()

async def run_benchmark():
    await setup_db()

    async with TestingSessionLocal() as session:
        # warmup
        await api_stats(db=session)

        start = time.time()
        for _ in range(100):
            await api_stats(db=session)
        end = time.time()
        print(f"Time for 100 calls: {end - start:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
