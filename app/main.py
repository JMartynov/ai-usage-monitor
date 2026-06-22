import contextlib
import os
import secrets
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

security = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    expected_api_key = os.environ.get("PROXY_API_KEY")
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: PROXY_API_KEY is missing."
        )

    if not secrets.compare_digest(
        credentials.credentials.encode('utf8'),
        expected_api_key.encode('utf8')
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@app.post("/v1/chat/completions")
async def proxy_chat_completions(
    payload: dict,  # Accept dict directly to avoid dropping fields
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    # Extract headers
    headers = dict(request.headers)

    # Send to proxy service
    return await forward_and_log(
        payload=payload,
        headers=headers,
        db=db
    )
