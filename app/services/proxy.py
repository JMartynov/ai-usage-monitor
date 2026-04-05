import json
import time
import uuid
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import RequestLog
from .pricing import calculate_cost

import os

OPENAI_API_URL = os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")

async def forward_and_log(
    payload: dict,
    headers: dict,
    db: AsyncSession,
) -> Response:
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Filter headers (keep Authorization, omit Host, Content-Length)
    proxy_headers = {
        k: v for k, v in headers.items()
        if k.lower() not in ("host", "content-length", "connection", "accept-encoding")
    }

    model = payload.get("model", "unknown")
    messages = payload.get("messages", [])
    prompt_text = json.dumps(messages)

    upstream_status = 500
    upstream_response_text = None
    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    error_message = None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENAI_API_URL,
                json=payload,
                headers=proxy_headers,
                timeout=60.0
            )
            upstream_status = response.status_code
            upstream_response_text = response.text

            if response.status_code == 200:
                resp_json = response.json()
                usage = resp_json.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens")
                completion_tokens = usage.get("completion_tokens")
                total_tokens = usage.get("total_tokens")
            else:
                error_message = f"Upstream error {response.status_code}"

    except Exception as e:
        error_message = str(e)
        upstream_response_text = json.dumps({"error": str(e)})
        upstream_status = 502

    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)

    estimated_cost = None
    if not error_message and prompt_tokens is not None and completion_tokens is not None:
        estimated_cost = calculate_cost(
            model,
            prompt_tokens,
            completion_tokens
        )

    # Log to database
    log_entry = RequestLog(
        request_id=request_id,
        model=model,
        prompt=prompt_text,
        response=upstream_response_text if not error_message else None,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        latency_ms=latency_ms,
        error=error_message,
    )

    db.add(log_entry)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        # In a real app we'd log this fallback error

    if error_message and upstream_status == 502:
        return JSONResponse(status_code=502, content={"error": error_message})

    return Response(
        content=upstream_response_text,
        status_code=upstream_status,
        headers={"Content-Type": "application/json"}
    )
