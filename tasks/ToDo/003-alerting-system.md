# 🚨 Task: Alerting System — Budget Limits + Anomaly Detection

## 🎯 Objective

Detect and react to:
* 💰 Budget overruns
* 📈 Cost spikes
* ⚠️ Abnormal usage patterns

Transform your system from:
→ passive dashboard
→ **active cost control system**

---

# 🧱 1. Alert Types (MANDATORY)

## 🔹 1.1 Daily Budget Alerts

### Rule
Trigger when:
```
daily_cost > DAILY_BUDGET
```

### Recommended threshold
* Start with: **1.5–2× average daily spend** ([AI Cost Board][1])

---

## 🔹 1.2 Monthly Budget Alerts

### Rules
* Warning:
```
monthly_cost >= 0.8 * MONTHLY_BUDGET
```

* Critical:
```
monthly_cost >= 0.95 * MONTHLY_BUDGET
```

---

## 🔹 1.3 Per-Request Cost Alerts

Trigger when:
```
request_cost > HIGH_COST_THRESHOLD
```

Example:
```python
HIGH_COST_THRESHOLD = 0.05  # $0.05 per request
```

👉 Detects:
* huge prompts
* large context windows
* runaway agents

---

## 🔹 1.4 Anomaly Detection Alerts (CORE FEATURE)

### Why needed
LLM costs don’t grow smoothly — they spike suddenly due to:
* prompt bugs
* retry loops
* user behavior bursts ([StackSpend][2])

---

# 🧠 2. Anomaly Detection Logic

## Approach: Baseline + Deviation

### Step 1: Compute baseline
```python
avg_cost_last_7_days
avg_tokens_last_7_days
```

---

### Step 2: Detect anomaly

#### Cost spike
```python
if today_cost > avg_cost * 2:
    trigger_alert("cost_spike")
```

#### Token anomaly
```python
if avg_tokens_per_request_today > baseline * 2:
    trigger_alert("token_anomaly")
```

---

## 📊 Advanced Signals (HIGH VALUE)

Track anomalies on:

### 1. Tokens per request
→ detects prompt/context explosion

### 2. Requests per minute
→ detects traffic spikes

### 3. Cost per hour
→ detects sudden spend bursts

### 4. Model usage shift
→ expensive model suddenly used more

These are **leading indicators**, not just totals ([Amestris][3])

---

# ⚙️ 3. Configuration (REQUIRED)

Create:
`app/config/alerts.py`

```python
ALERT_CONFIG = {
    "daily_budget": 10.0,
    "monthly_budget": 200.0,

    "cost_spike_multiplier": 2.0,
    "token_spike_multiplier": 2.0,

    "high_cost_request": 0.05
}
```

---

# 🔔 4. Alert Engine (Core Service)

`app/services/alerts.py`

```python
def evaluate_alerts(stats):
    alerts = []

    # Daily budget
    if stats.daily_cost > CONFIG["daily_budget"]:
        alerts.append("DAILY_BUDGET_EXCEEDED")

    # Monthly budget
    if stats.monthly_cost > CONFIG["monthly_budget"] * 0.95:
        alerts.append("MONTHLY_CRITICAL")

    # Cost anomaly
    if stats.daily_cost > stats.avg_daily_cost * CONFIG["cost_spike_multiplier"]:
        alerts.append("COST_ANOMALY")

    return alerts
```

---

# 📡 5. Alert Delivery (MVP)

## Required
* Log alerts to DB
* Expose API:
```
GET /alerts
```

## Optional (Recommended)
### Webhook support
```python
POST webhook_url
{
  "type": "COST_SPIKE",
  "value": 23.5
}
```

---

# 🗄️ 6. Database Table

### Table: `alerts`

| Column     | Type     |
| ---------- | -------- |
| id         | Integer  |
| type       | String   |
| message    | Text     |
| severity   | String   |
| created_at | DateTime |

---

# 🧪 7. Testing (MANDATORY)

## Cases
* [ ] Daily budget exceeded triggers alert
* [ ] Monthly threshold triggers warning + critical
* [ ] Cost spike (2× baseline) triggers alert
* [ ] Normal usage does NOT trigger alert
* [ ] High-cost request triggers alert

---

# 🧠 8. Guardrails (VERY IMPORTANT)

Detection alone is not enough.

Add **automatic protections**:

### 1. Hard budget cutoff
```python
if monthly_cost > budget:
    block_requests = True
```

### 2. Model downgrade
```python
if budget_exceeded:
    switch_to("gpt-4o-mini")
```

### 3. Rate limiting
* max requests/minute
* max tokens/request

👉 These are critical because:
> cost anomalies should be treated like incidents, not reports ([Amestris][3])

---

# 📊 9. Dashboard Integration

Add:
* alert banner (top of dashboard)
* alert history panel
* severity colors:
  * 🔴 critical
  * 🟡 warning
  * 🔵 info

---

# 🚀 Final System Architecture

```
App → Proxy → LLM
        ↓
     Logging → DB
        ↓
   Aggregation → Alerts Engine
        ↓
     Dashboard + Webhooks
```

---

# 🔥 Key Insight

Most teams fail because:
* they track averages
* but **cost problems come from spikes**

👉 A single bug can multiply cost 5× in hours ([AI Cost Board][1])

---

# ⏱️ Implementation Effort

* Basic alerts: 2–3 hours
* Anomaly detection: +2 hours
* Webhooks + UI: +2–4 hours

---

[1]: https://aicostboard.com/blog/posts/set-up-llm-cost-alerts?utm_source=chatgpt.com "How to Set Up LLM Cost Alerts and Prevent Budget Overruns | AI Cost Board"
[2]: https://www.stackspend.app/ai-cost-anomaly-detection?utm_source=chatgpt.com "AI Cost Anomaly Detection Software — StackSpend"
[3]: https://amestris.com.au/blog/llm-cost-anomaly-detection.html?utm_source=chatgpt.com "LLM Cost Anomaly Detection: Budgets, Token Explosions and Rapid Triage | Amestris"
