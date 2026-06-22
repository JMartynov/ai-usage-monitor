import asyncio
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, func
from app.models import Base, RequestLog
import uuid
import datetime

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # no rows
        totals_query = await session.execute(
            select(
                func.count(RequestLog.id),
                func.sum(RequestLog.total_tokens),
                func.sum(RequestLog.estimated_cost)
            )
        )
        result = totals_query.one()
        print(result)

        total_requests, total_tokens, total_cost = result
        total_tokens = total_tokens or 0
        total_cost = total_cost or 0.0
        print(f"requests={total_requests}, tokens={total_tokens}, cost={total_cost}")

if __name__ == "__main__":
    asyncio.run(main())
