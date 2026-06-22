import asyncio
import time
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.models import Base, RequestLog
from app.routers.dashboard import api_stats
import uuid
import datetime

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def setup_db():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # insert 10k rows
        logs = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for i in range(10000):
            logs.append(
                RequestLog(
                    id=i+1, # Integer
                    request_id=str(uuid.uuid4()),
                    model="gpt-4",
                    prompt_tokens=100,
                    completion_tokens=200,
                    total_tokens=300,
                    estimated_cost=0.01,
                    prompt="Hello",
                    response="Hi",
                    timestamp=now
                )
            )
        session.add_all(logs)
        await session.commit()

    return async_session

async def benchmark():
    async_session = await setup_db()

    # warmup
    async with async_session() as session:
        await api_stats(session)

    # run
    runs = 10
    start = time.perf_counter()
    for _ in range(runs):
        async with async_session() as session:
            await api_stats(session)
    end = time.perf_counter()

    print(f"Average time over {runs} runs: {(end - start) / runs * 1000:.2f} ms")

if __name__ == "__main__":
    asyncio.run(benchmark())
