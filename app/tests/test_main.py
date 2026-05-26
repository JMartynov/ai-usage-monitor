import pytest
from sqlalchemy import inspect

from app.main import lifespan, app as main_app
from app.database import engine, Base


@pytest.mark.asyncio
async def test_lifespan_creates_tables():
    """
    Test that the lifespan context manager creates database tables on startup.
    We test it by directly invoking the lifespan function which acts as an
    async context manager.
    """
    # 1. Drop all tables first to ensure a clean state
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Verify tables are dropped
    def get_table_names(connection):
        return inspect(connection).get_table_names()

    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)
        assert "requests" not in tables

    # 2. Invoke the lifespan context manager directly
    # Note: ASGITransport doesn't trigger the lifespan events natively, so we
    # explicitly test the lifespan function which main_app is using.
    async with lifespan(main_app):
        # 3. Verify tables are created
        async with engine.connect() as conn:
            tables = await conn.run_sync(get_table_names)
            assert "requests" in tables

    # Clean up (to leave DB state clean for other tests)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
