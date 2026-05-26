import asyncio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text

from ..database import get_db
from ..models import RequestLog
from typing import Dict, Any

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/api/stats")
async def api_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    # We will use the bind/engine from the provided db session to create
    # fresh connections. This allows concurrency without violating session
    # thread-safety, AND it respects the test dependency overrides since
    # db.bind will point to the memory test engine!

    engine = db.bind

    async def get_total_requests():
        async with engine.connect() as conn:
            query = await conn.execute(select(func.count(RequestLog.id)))
            return query.scalar_one()

    async def get_total_tokens():
        async with engine.connect() as conn:
            q = select(func.sum(RequestLog.total_tokens))
            query = await conn.execute(q)
            return query.scalar_one() or 0

    async def get_total_cost():
        async with engine.connect() as conn:
            q = select(func.sum(RequestLog.estimated_cost))
            query = await conn.execute(q)
            return query.scalar_one() or 0.0

    async def get_cost_over_time():
        async with engine.connect() as conn:
            query = await conn.execute(
                select(
                    func.date(RequestLog.timestamp).label("date"),
                    func.sum(RequestLog.estimated_cost).label("daily_cost")
                ).group_by(text("date")).order_by(text("date"))
            )
            return [
                {"date": str(row.date), "cost": float(row.daily_cost or 0)}
                for row in query
            ]

    async def get_model_distribution():
        async with engine.connect() as conn:
            query = await conn.execute(
                select(
                    RequestLog.model,
                    func.count(RequestLog.id).label("request_count"),
                    func.sum(RequestLog.total_tokens).label("tokens"),
                    func.sum(RequestLog.estimated_cost).label("cost")
                ).group_by(RequestLog.model)
            )
            return [
                {
                    "model": row.model,
                    "requests": row.request_count,
                    "tokens": int(row.tokens or 0),
                    "cost": float(row.cost or 0)
                }
                for row in query
            ]

    async def get_token_breakdown():
        async with engine.connect() as conn:
            query = await conn.execute(
                select(
                    func.sum(RequestLog.prompt_tokens).label("input_tokens"),
                    func.sum(RequestLog.completion_tokens).label(
                        "output_tokens"
                    )
                )
            )
            result = query.first()
            return {
                "input": int(result.input_tokens or 0) if result else 0,
                "output": int(result.output_tokens or 0) if result else 0
            }

    async def get_recent_activity():
        async with engine.connect() as conn:
            query = await conn.execute(
                select(
                    RequestLog.id,
                    RequestLog.model,
                    RequestLog.prompt,
                    RequestLog.estimated_cost,
                    RequestLog.timestamp
                ).order_by(desc(RequestLog.timestamp)).limit(20)
            )
            return [
                {
                    "id": row.id,
                    "model": row.model,
                    "prompt": (
                        (row.prompt[:97] + "...")
                        if row.prompt and len(row.prompt) > 100
                        else row.prompt
                    ),
                    "cost": float(row.estimated_cost or 0),
                    "timestamp": (
                        row.timestamp.isoformat()
                        if hasattr(row.timestamp, 'isoformat')
                        else str(row.timestamp)
                    )
                }
                for row in query
            ]

    async def get_expensive_requests():
        async with engine.connect() as conn:
            query = await conn.execute(
                select(
                    RequestLog.id,
                    RequestLog.model,
                    RequestLog.estimated_cost,
                    RequestLog.total_tokens,
                    RequestLog.timestamp
                ).order_by(desc(RequestLog.estimated_cost)).limit(10)
            )
            return [
                {
                    "id": row.id,
                    "model": row.model,
                    "cost": float(row.estimated_cost or 0),
                    "tokens": int(row.total_tokens or 0),
                    "timestamp": (
                        row.timestamp.isoformat()
                        if hasattr(row.timestamp, 'isoformat')
                        else str(row.timestamp)
                    )
                }
                for row in query
            ]

    results = await asyncio.gather(
        get_total_requests(),
        get_total_tokens(),
        get_total_cost(),
        get_cost_over_time(),
        get_model_distribution(),
        get_token_breakdown(),
        get_recent_activity(),
        get_expensive_requests()
    )

    return {
        "total": {
            "requests": results[0],
            "tokens": int(results[1]),
            "cost": float(results[2])
        },
        "cost_over_time": results[3],
        "model_distribution": results[4],
        "token_breakdown": results[5],
        "recent_activity": results[6],
        "expensive_requests": results[7]
    }


@router.get("/api/alerts")
async def api_alerts(db: AsyncSession = Depends(get_db)):
    # Simple alert logic: any request costing > $1.00 or > 100000 tokens
    cost_threshold = 1.00
    tokens_threshold = 100000

    alerts_query = await db.execute(
        select(RequestLog)
        .where(
            (RequestLog.estimated_cost > cost_threshold) |
            (RequestLog.total_tokens > tokens_threshold)
        )
        .order_by(desc(RequestLog.timestamp))
        .limit(50)
    )

    alerts = []
    for row in alerts_query.scalars():
        alert_type = "cost" if (
            row.estimated_cost and row.estimated_cost > cost_threshold
        ) else "budget"

        cost_display = (
            f"{row.estimated_cost}$" if row.estimated_cost is not None
            else "Unknown cost"
        )

        reason = 'cost' if alert_type == 'cost' else 'token usage'
        message = (
            f"High {reason} detected: {cost_display} / "
            f"{row.total_tokens} tokens"
        )

        alerts.append({
            "id": row.id,
            "type": alert_type,
            "model": row.model,
            "cost": float(row.estimated_cost or 0),
            "tokens": int(row.total_tokens or 0),
            "timestamp": row.timestamp.isoformat(),
            "message": message
        })

    return alerts
