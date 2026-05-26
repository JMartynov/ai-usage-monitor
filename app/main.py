import contextlib
from fastapi import FastAPI, Depends, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, Base, get_db
from .services.proxy import forward_and_log
from .routers.dashboard import router as dashboard_router


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(dashboard_router)


@app.post("/v1/chat/completions")
async def proxy_chat_completions(
    payload: dict,  # Accept dict directly to avoid dropping fields
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Extract headers
    headers = dict(request.headers)

    # Send to proxy service
    return await forward_and_log(
        payload=payload,
        headers=headers,
        background_tasks=background_tasks,
        db=db
    )
