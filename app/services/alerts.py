from ..config.alerts import ALERT_CONFIG


def evaluate_alerts(stats):
    alerts = []

    # Daily budget
    if getattr(stats, "daily_cost", 0) > ALERT_CONFIG["daily_budget"]:
        alerts.append(
            {
                "type": "DAILY_BUDGET_EXCEEDED",
                "message": f"Daily budget exceeded: {
                    stats.daily_cost} > {
                    ALERT_CONFIG['daily_budget']}",
                "severity": "critical"})

    # Monthly budget
    if getattr(
        stats,
        "monthly_cost",
            0) > ALERT_CONFIG["monthly_budget"] * 0.95:
        alerts.append(
            {
                "type": "MONTHLY_CRITICAL",
                "message": f"Monthly budget critical: {
                    stats.monthly_cost} > {
                    ALERT_CONFIG['monthly_budget'] *
                    0.95}",
                "severity": "critical"})
    elif getattr(
        stats, "monthly_cost", 0
    ) > ALERT_CONFIG["monthly_budget"] * 0.8:
        alerts.append(
            {
                "type": "MONTHLY_WARNING",
                "message": f"Monthly budget warning: {
                    stats.monthly_cost} > {
                    ALERT_CONFIG['monthly_budget'] *
                    0.8}",
                "severity": "warning"})

    # Cost anomaly
    if getattr(
        stats,
        "daily_cost",
        0) > getattr(
        stats,
        "avg_daily_cost",
            float('inf')) * ALERT_CONFIG["cost_spike_multiplier"]:
        alerts.append(
            {
                "type": "COST_ANOMALY",
                "message": f"Cost anomaly detected: daily_cost {
                    stats.daily_cost} > avg_daily_cost {
                    stats.avg_daily_cost} * {
                    ALERT_CONFIG['cost_spike_multiplier']}",
                "severity": "warning"})

    # High cost request
    if getattr(stats, "request_cost", 0) > ALERT_CONFIG["high_cost_request"]:
        alerts.append(
            {
                "type": "HIGH_COST_REQUEST",
                "message": f"High cost request: {
                    stats.request_cost} > {
                    ALERT_CONFIG['high_cost_request']}",
                "severity": "warning"})

    # Token anomaly
    if getattr(
        stats,
        "avg_tokens_per_request_today",
        0) > getattr(
        stats,
        "baseline_tokens_per_request",
            float('inf')) * ALERT_CONFIG["token_spike_multiplier"]:
        alerts.append(
            {
                "type": "TOKEN_ANOMALY",
                "message": f"Token anomaly detected: {
                    stats.avg_tokens_per_request_today} > {
                    stats.baseline_tokens_per_request} * {
                    ALERT_CONFIG['token_spike_multiplier']}",
                "severity": "warning"})

    return alerts
