from app.services.alerts import evaluate_alerts
from app.config.alerts import ALERT_CONFIG


class MockStats:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_daily_budget_exceeded():
    stats = MockStats(daily_cost=ALERT_CONFIG["daily_budget"] + 1)
    alerts = evaluate_alerts(stats)

    assert len(alerts) > 0
    assert any(a["type"] == "DAILY_BUDGET_EXCEEDED" for a in alerts)


def test_monthly_critical():
    stats = MockStats(monthly_cost=ALERT_CONFIG["monthly_budget"] * 0.96)
    alerts = evaluate_alerts(stats)

    assert len(alerts) > 0
    assert any(a["type"] == "MONTHLY_CRITICAL" for a in alerts)


def test_monthly_warning():
    stats = MockStats(monthly_cost=ALERT_CONFIG["monthly_budget"] * 0.85)
    alerts = evaluate_alerts(stats)

    assert len(alerts) > 0
    assert any(a["type"] == "MONTHLY_WARNING" for a in alerts)


def test_cost_anomaly():
    stats = MockStats(
        daily_cost=10,
        avg_daily_cost=4,
        request_cost=0.01,
        avg_tokens_per_request_today=50,
        baseline_tokens_per_request=50
    )
    # 10 > 4 * 2.0 (ALERT_CONFIG["cost_spike_multiplier"])
    alerts = evaluate_alerts(stats)

    assert len(alerts) > 0
    assert any(a["type"] == "COST_ANOMALY" for a in alerts)


def test_high_cost_request():
    stats = MockStats(request_cost=ALERT_CONFIG["high_cost_request"] + 0.01)
    alerts = evaluate_alerts(stats)

    assert len(alerts) > 0
    assert any(a["type"] == "HIGH_COST_REQUEST" for a in alerts)


def test_normal_usage_no_alerts():
    stats = MockStats(
        daily_cost=2,
        monthly_cost=50,
        avg_daily_cost=2,
        request_cost=0.01,
        avg_tokens_per_request_today=100,
        baseline_tokens_per_request=100
    )
    alerts = evaluate_alerts(stats)
    assert len(alerts) == 0
