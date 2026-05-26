import json
import time
import uuid
import httpx
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Optional, Dict, Any
from ..models import RequestLog
from .pricing import calculate_cost

import os

OPENAI_API_URL = os.environ.get(
    "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
)


def _filter_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Filters out headers that should not be forwarded."""
    return {
        k: v for k, v in headers.items()
        if k.lower() not in (
            "host",
            "content-length",
            "connection",
            "accept-encoding"
        )
    }


async def _make_upstream_request(
    payload: Dict[str, Any],
    headers: Dict[str, str]
) -> Tuple[int, Optional[str], Optional[str]]:
    """Makes the request to the upstream API.
    Returns: (status_code, response_text, error_message)
    """
    proxy_headers = _filter_headers(headers)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENAI_API_URL,
                json=payload,
                headers=proxy_headers,
                timeout=60.0
            )

            if response.status_code == 200:
                return response.status_code, response.text, None

            return (
                response.status_code,
                response.text,
                f"Upstream error {response.status_code}"
            )

    except Exception as e:
        return 502, json.dumps({"error": str(e)}), str(e)


def _parse_usage(
    status_code: int,
    response_text: Optional[str]
) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """Parses token usage from the upstream response.
    Returns: (prompt_tokens, completion_tokens, total_tokens)
    """
    if status_code == 200 and response_text:
        try:
            resp_json = json.loads(response_text)
            usage = resp_json.get("usage", {})
            return (
                usage.get("prompt_tokens"),
                usage.get("completion_tokens"),
                usage.get("total_tokens")
            )
        except json.JSONDecodeError:
            pass

    return None, None, None


async def _log_request(
    db: AsyncSession,
    request_id: str,
    model: str,
    prompt_text: str,
    response_text: Optional[str],
    prompt_tokens: Optional[int],
    completion_tokens: Optional[int],
    total_tokens: Optional[int],
    estimated_cost: Optional[float],
    latency_ms: int,
    error_message: Optional[str]
) -> None:
    """Logs the request details to the database."""
    log_entry = RequestLog(
        request_id=request_id,
        model=model,
        prompt=prompt_text,
        response=response_text if not error_message else None,
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
    except Exception:
        await db.rollback()
        # In a real app we'd log this fallback error


async def forward_and_log(
    payload: Dict[str, Any],
    headers: Dict[str, str],
    db: AsyncSession,
) -> Response:
    """Forwards a request to the upstream API and logs it."""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    model = payload.get("model", "unknown")
    messages = payload.get("messages", [])
    prompt_text = json.dumps(messages)

    result = await _make_upstream_request(payload, headers)
    upstream_status, upstream_response_text, error_message = result

    prompt_tokens, completion_tokens, total_tokens = _parse_usage(
        upstream_status, upstream_response_text
    )

    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)

    estimated_cost = None
    if (not error_message and
            prompt_tokens is not None and
            completion_tokens is not None):
        estimated_cost = calculate_cost(
            model,
            prompt_tokens,
            completion_tokens
        )

    await _log_request(
        db=db,
        request_id=request_id,
        model=model,
        prompt_text=prompt_text,
        response_text=upstream_response_text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=estimated_cost,
        latency_ms=latency_ms,
        error_message=error_message
    )

    if error_message and upstream_status == 502:
        return JSONResponse(status_code=502, content={"error": error_message})

    return Response(
        content=upstream_response_text,
        status_code=upstream_status,
        headers={"Content-Type": "application/json"}
    )
