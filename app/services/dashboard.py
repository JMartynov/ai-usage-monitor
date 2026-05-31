from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text

from app.models import RequestLog


async def get_total_usage(db: AsyncSession) -> Dict[str, Any]:
    total_requests_query = await db.execute(select(func.count(RequestLog.id)))
    total_requests = total_requests_query.scalar_one()

    total_tokens_query = await db.execute(
        select(func.sum(RequestLog.total_tokens)))
    total_tokens = total_tokens_query.scalar_one() or 0

    total_cost_query = await db.execute(
        select(func.sum(RequestLog.estimated_cost)))
    total_cost = total_cost_query.scalar_one() or 0.0

    return {
        "requests": total_requests,
        "tokens": int(total_tokens),
        "cost": float(total_cost)
    }


async def get_cost_over_time(db: AsyncSession) -> List[Dict[str, Any]]:
    # Using raw SQL for sqlite compatibility
    cost_over_time_query = await db.execute(
        select(
            func.date(RequestLog.timestamp).label("date"),
            func.sum(RequestLog.estimated_cost).label("daily_cost")
        ).group_by(text("date")).order_by(text("date"))
    )
    return [
        {"date": str(row.date), "cost": float(row.daily_cost or 0)}
        for row in cost_over_time_query
    ]


async def get_model_distribution(db: AsyncSession) -> List[Dict[str, Any]]:
    model_dist_query = await db.execute(
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
        for row in model_dist_query
    ]


async def get_token_breakdown(db: AsyncSession) -> Dict[str, Any]:
    token_breakdown_query = await db.execute(
        select(
            func.sum(RequestLog.prompt_tokens).label("input_tokens"),
            func.sum(RequestLog.completion_tokens).label("output_tokens")
        )
    )
    token_breakdown_result = token_breakdown_query.first()
    return {
        "input": int(
            token_breakdown_result.input_tokens or 0
        ) if token_breakdown_result else 0,
        "output": int(
            token_breakdown_result.output_tokens or 0
        ) if token_breakdown_result else 0
    }


async def get_recent_activity(db: AsyncSession) -> List[Dict[str, Any]]:
    recent_activity_query = await db.execute(
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
            "timestamp": row.timestamp.isoformat()
        }
        for row in recent_activity_query
    ]


async def get_expensive_requests(db: AsyncSession) -> List[Dict[str, Any]]:
    expensive_requests_query = await db.execute(
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
            "timestamp": row.timestamp.isoformat()
        }
        for row in expensive_requests_query
    ]


async def get_alerts(db: AsyncSession) -> List[Dict[str, Any]]:
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
