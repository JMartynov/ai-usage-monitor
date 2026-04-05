from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text

from ..database import get_db
from ..models import RequestLog
from typing import Dict, Any
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@router.get("/api/stats")
async def api_stats(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    # 1. Total Usage
    total_requests_query = await db.execute(select(func.count(RequestLog.id)))
    total_requests = total_requests_query.scalar_one()

    total_tokens_query = await db.execute(select(func.sum(RequestLog.total_tokens)))
    total_tokens = total_tokens_query.scalar_one() or 0

    total_cost_query = await db.execute(select(func.sum(RequestLog.estimated_cost)))
    total_cost = total_cost_query.scalar_one() or 0.0

    # 2. Cost Over Time (grouped by day)
    # Using raw SQL for sqlite compatibility
    cost_over_time_query = await db.execute(
        select(
            func.date(RequestLog.timestamp).label("date"),
            func.sum(RequestLog.estimated_cost).label("daily_cost")
        ).group_by(text("date")).order_by(text("date"))
    )
    cost_over_time = [
        {"date": str(row.date), "cost": float(row.daily_cost or 0)}
        for row in cost_over_time_query
    ]

    # 3. Model Distribution
    model_dist_query = await db.execute(
        select(
            RequestLog.model,
            func.count(RequestLog.id).label("request_count"),
            func.sum(RequestLog.total_tokens).label("tokens"),
            func.sum(RequestLog.estimated_cost).label("cost")
        ).group_by(RequestLog.model)
    )
    model_distribution = [
        {
            "model": row.model,
            "requests": row.request_count,
            "tokens": int(row.tokens or 0),
            "cost": float(row.cost or 0)
        }
        for row in model_dist_query
    ]

    # 4. Token Breakdown
    token_breakdown_query = await db.execute(
        select(
            func.sum(RequestLog.prompt_tokens).label("input_tokens"),
            func.sum(RequestLog.completion_tokens).label("output_tokens")
        )
    )
    token_breakdown_result = token_breakdown_query.first()
    token_breakdown = {
        "input": int(token_breakdown_result.input_tokens or 0) if token_breakdown_result else 0,
        "output": int(token_breakdown_result.output_tokens or 0) if token_breakdown_result else 0
    }

    # 5. Recent Activity Feed (last 20)
    recent_activity_query = await db.execute(
        select(
            RequestLog.id,
            RequestLog.model,
            RequestLog.prompt,
            RequestLog.estimated_cost,
            RequestLog.timestamp
        ).order_by(desc(RequestLog.timestamp)).limit(20)
    )
    recent_activity = [
        {
            "id": row.id,
            "model": row.model,
            "prompt": (row.prompt[:100] + "...") if row.prompt and len(row.prompt) > 100 else row.prompt,
            "cost": float(row.estimated_cost or 0),
            "timestamp": row.timestamp.isoformat()
        }
        for row in recent_activity_query
    ]

    # 6. Top Expensive Requests
    expensive_requests_query = await db.execute(
        select(
            RequestLog.id,
            RequestLog.model,
            RequestLog.estimated_cost,
            RequestLog.total_tokens,
            RequestLog.timestamp
        ).order_by(desc(RequestLog.estimated_cost)).limit(10)
    )
    expensive_requests = [
        {
            "id": row.id,
            "model": row.model,
            "cost": float(row.estimated_cost or 0),
            "tokens": int(row.total_tokens or 0),
            "timestamp": row.timestamp.isoformat()
        }
        for row in expensive_requests_query
    ]

    return {
        "total": {
            "requests": total_requests,
            "tokens": int(total_tokens),
            "cost": float(total_cost)
        },
        "cost_over_time": cost_over_time,
        "model_distribution": model_distribution,
        "token_breakdown": token_breakdown,
        "recent_activity": recent_activity,
        "expensive_requests": expensive_requests
    }
