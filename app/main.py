import contextlib
from fastapi import FastAPI, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, Base, get_db
from .services.proxy import forward_and_log
from .routers.dashboard import router as dashboard_router


import httpx


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize httpx client for proxy
    app.state.client = httpx.AsyncClient()

    yield

    # Cleanup httpx client
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)

app.include_router(dashboard_router)


@app.post("/v1/chat/completions")
async def proxy_chat_completions(
    payload: dict,  # Accept dict directly to avoid dropping fields
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Extract headers
    headers = dict(request.headers)

    client = request.app.state.client

    # Send to proxy service
    return await forward_and_log(
        payload=payload, headers=headers, db=db, client=client
    )
