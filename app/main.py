import contextlib
from fastapi import FastAPI, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, Base, get_db
from .schemas import ChatCompletionRequest
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
    payload: ChatCompletionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Extract headers
    headers = dict(request.headers)

    # Send to proxy service
    return await forward_and_log(
        payload=payload.model_dump(exclude_unset=True),
        headers=headers,
        db=db
    )
