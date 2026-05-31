from fastapi import APIRouter, Depends, Request

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.dashboard import (
    get_total_usage,
    get_cost_over_time,
    get_model_distribution,
    get_token_breakdown,
    get_recent_activity,
    get_expensive_requests,
    get_alerts
)
from typing import Dict, Any

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
    return await get_alerts(db)
