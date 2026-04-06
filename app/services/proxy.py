import datetime
import json
import time
import uuid
import httpx
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models import RequestLog, Alert
from .pricing import calculate_cost
from .alerts import evaluate_alerts
from ..config.alerts import ALERT_CONFIG

import os

OPENAI_API_URL = os.environ.get(
    "OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"
)


class StatsMock:
    pass


async def forward_and_log(
    payload: dict,
    headers: dict,
    db: AsyncSession,
) -> Response:
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # --- Guardrails / Pre-request Checks ---
    # Calculate current stats for guardrails
    stats = StatsMock()

    now = datetime.datetime.now(datetime.timezone.utc)
    start_of_month = now.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    one_minute_ago = now - datetime.timedelta(minutes=1)

    # 1. Rate Limiting: max requests/minute
    requests_last_minute_query = await db.execute(
        select(func.count(RequestLog.id))
        .where(RequestLog.timestamp >= one_minute_ago)
    )
    requests_last_minute = requests_last_minute_query.scalar_one() or 0
    if requests_last_minute >= ALERT_CONFIG["max_requests_per_minute"]:
        return JSONResponse(
            status_code=429, content={
                "error": "Rate limit exceeded. Too many requests per minute."})

    monthly_cost_query = await db.execute(
        select(func.sum(RequestLog.estimated_cost))
        .where(RequestLog.timestamp >= start_of_month)
    )
    monthly_cost = monthly_cost_query.scalar_one() or 0.0
    stats.monthly_cost = monthly_cost

    if monthly_cost > ALERT_CONFIG["monthly_budget"]:
        return JSONResponse(
            status_code=429,
            content={"error": "Monthly budget exceeded. Request blocked."}
        )

    # Model downgrade if budget nearly exceeded (example)
    model = payload.get("model", "unknown")
    if monthly_cost > ALERT_CONFIG["monthly_budget"] * 0.95:
        if model != "gpt-4o-mini":  # Example downgrade logic
            payload["model"] = "gpt-4o-mini"
            model = "gpt-4o-mini"

    # 3. Rate Limiting: max tokens/request
    # For a robust proxy, we'd count actual tokens using tiktoken.
    # For MVP, we limit max_tokens param if requested, or block if very high.
    requested_max_tokens = payload.get("max_tokens")
    max_tkns_limit = ALERT_CONFIG["max_tokens_per_request"]
    if requested_max_tokens and requested_max_tokens > max_tkns_limit:
        payload["max_tokens"] = max_tkns_limit

    # Filter headers (keep Authorization, omit Host, Content-Length)
    proxy_headers = {
        k: v for k,
        v in headers.items() if k.lower() not in (
            "host",
            "content-length",
            "connection",
            "accept-encoding")}

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
    if not error_message and prompt_tokens is not None and \
            completion_tokens is not None:
        estimated_cost = calculate_cost(
            model,
            prompt_tokens,
            completion_tokens
        )

    # --- Background Alerting Evaluation ---
    if estimated_cost is not None:
        # Calculate daily cost
        daily_cost_query = await db.execute(
            select(func.sum(RequestLog.estimated_cost))
            .where(RequestLog.timestamp >= start_of_day)
        )
        daily_cost = daily_cost_query.scalar_one() or 0.0
        stats.daily_cost = daily_cost + estimated_cost

        # Calculate averages for anomalies
        seven_days_ago = now - datetime.timedelta(days=7)

        avg_daily_query = await db.execute(
            select(
                func.sum(RequestLog.estimated_cost)
            ).where(RequestLog.timestamp >= seven_days_ago)
        )
        total_7_days = avg_daily_query.scalar_one() or 0.0
        stats.avg_daily_cost = total_7_days / 7.0 if total_7_days > 0 else 0.0

        # Request cost
        stats.request_cost = estimated_cost

        # Token anomaly
        tokens_today_query = await db.execute(
            select(func.avg(RequestLog.total_tokens))
            .where(RequestLog.timestamp >= start_of_day)
        )
        avg_tokens_today = tokens_today_query.scalar_one() or 0.0

        # Approximate average tokens per request today if we include this one
        requests_today_query = await db.execute(
            select(func.count(RequestLog.id))
            .where(RequestLog.timestamp >= start_of_day)
        )
        requests_today = requests_today_query.scalar_one() or 0
        total_tokens_today = (
            avg_tokens_today * requests_today) + (total_tokens or 0)
        stats.avg_tokens_per_request_today = total_tokens_today / \
            (requests_today + 1)

        avg_tokens_baseline_query = await db.execute(
            select(func.avg(RequestLog.total_tokens))
            .where(RequestLog.timestamp >= seven_days_ago)
            .where(RequestLog.timestamp < start_of_day)
        )
        baseline_res = avg_tokens_baseline_query.scalar_one()
        stats.baseline_tokens_per_request = baseline_res or 0.0

        alerts = evaluate_alerts(stats)
        for alert_dict in alerts:
            new_alert = Alert(
                type=alert_dict["type"],
                message=alert_dict["message"],
                severity=alert_dict["severity"],
            )
            db.add(new_alert)

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
    except Exception:
        await db.rollback()
        # In a real app we'd log this fallback error

    if error_message and upstream_status == 502:
        return JSONResponse(status_code=502, content={"error": error_message})

    return Response(
        content=upstream_response_text,
        status_code=upstream_status,
        headers={"Content-Type": "application/json"}
    )
