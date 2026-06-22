import asyncio
from sqlalchemy import select, func, desc
from app.database import engine, Base
from app.models import RequestLog
from sqlalchemy.ext.asyncio import AsyncSession
import time
import uuid

async def setup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        for i in range(100):
            long_prompt = "A" * 50000 # 50KB prompt
            log = RequestLog(
                model="test",
                prompt=long_prompt,
                estimated_cost=0.01,
                total_tokens=10,
                prompt_tokens=5,
                completion_tokens=5
            )
            session.add(log)
        await session.commit()

async def bench_old():
    async with AsyncSession(engine) as session:
        start = time.time()
        for _ in range(50):
            q = await session.execute(
                select(
                    RequestLog.id,
                    RequestLog.model,
                    RequestLog.prompt,
                    RequestLog.estimated_cost,
                    RequestLog.timestamp
                ).order_by(desc(RequestLog.timestamp)).limit(20)
            )
            res = [
                {
                    "prompt": (row.prompt[:97] + "...") if row.prompt and len(row.prompt) > 100 else row.prompt
                }
                for row in q
            ]
        return time.time() - start

async def bench_new():
    async with AsyncSession(engine) as session:
        start = time.time()
        for _ in range(50):
            q = await session.execute(
                select(
                    RequestLog.id,
                    RequestLog.model,
                    func.substr(RequestLog.prompt, 1, 101).label("prompt"),
                    RequestLog.estimated_cost,
                    RequestLog.timestamp
                ).order_by(desc(RequestLog.timestamp)).limit(20)
            )
            res = [
                {
                    "prompt": (row.prompt[:97] + "...") if row.prompt and len(row.prompt) > 100 else row.prompt
                }
                for row in q
            ]
        return time.time() - start

async def main():
    await setup()
    old_time = await bench_old()
    new_time = await bench_new()
    print(f"Old time: {old_time:.4f}")
    print(f"New time: {new_time:.4f}")

asyncio.run(main())
