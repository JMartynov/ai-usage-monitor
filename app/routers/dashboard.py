from fastapi import APIRouter, Depends, Request

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ..database import get_db
from ..models import RequestLog
from typing import Dict, Any

from app.services.dashboard import (
    get_total_usage,
    get_cost_over_time,
    get_model_distribution,
    get_token_breakdown,
    get_recent_activity,
    get_expensive_requests,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")


@router.get("/api/stats")
async def api_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    total_usage = await get_total_usage(db)
    cost_over_time = await get_cost_over_time(db)
    model_distribution = await get_model_distribution(db)
    token_breakdown = await get_token_breakdown(db)
    recent_activity = await get_recent_activity(db)
    expensive_requests = await get_expensive_requests(db)

    return {
        "total": total_usage,
        "cost_over_time": cost_over_time,
        "model_distribution": model_distribution,
        "token_breakdown": token_breakdown,
        "recent_activity": recent_activity,
        "expensive_requests": expensive_requests
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
