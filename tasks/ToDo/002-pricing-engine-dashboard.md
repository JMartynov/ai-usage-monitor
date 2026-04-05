# 🚀 Task Extension: Pricing Engine + Dashboard (Single User)

---

# 💰 7. Model Pricing Configuration (NEW — REQUIRED)

## 🎯 Objective

Enable **accurate cost estimation per request** based on model and token usage.

---

## 📊 Background

LLM APIs are priced per token (input + output), and **output tokens are usually significantly more expensive than input tokens**.

---

## 🧱 Implementation

### 7.1 Pricing Config (Static Table)

Create a config file:
`app/config/pricing.py`

### Example:
```python
MODEL_PRICING = {
    "gpt-4o": {
        "input_per_1k": 0.0025,
        "output_per_1k": 0.01
    },
    "gpt-4o-mini": {
        "input_per_1k": 0.00015,
        "output_per_1k": 0.0006
    },
    "gpt-4.1": {
        "input_per_1k": 0.002,
        "output_per_1k": 0.008
    }
}
```

---

### 7.2 Default Pricing (MANDATORY)

Handle unknown models:
```python
DEFAULT_PRICING = {
    "input_per_1k": 0.002,
    "output_per_1k": 0.008
}
```

---

### 7.3 Cost Calculation Function
`app/services/pricing.py`

```python
def calculate_cost(model, prompt_tokens, completion_tokens):
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)

    input_cost = (prompt_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (completion_tokens / 1000) * pricing["output_per_1k"]

    return round(input_cost + output_cost, 6)
```

---

### 7.4 Database Update

Add column:
| Column         | Type  |
| -------------- | ----- |
| estimated_cost | Float |

---

### 7.5 Logging Integration

During response handling:
```python
cost = calculate_cost(
    model,
    usage["prompt_tokens"],
    usage["completion_tokens"]
)
```
Store in DB.

---

# 📊 8. Dashboard (Single User — Comprehensive MVP)

## 🎯 Objective

Provide **clear visibility into usage, cost, and behavior**

---

## 🧱 Architecture Options

### Option A (Recommended MVP)
* FastAPI + Jinja2 templates
* Chart.js for graphs

### Option B
* Separate React frontend

👉 Start with **Option A** (faster)

---

# 📈 8.1 Dashboard Endpoints

### GET `/dashboard`
Main UI

### GET `/api/stats`
Returns aggregated data

---

# 📊 8.2 Metrics to Implement (MANDATORY)

## 🔹 1. Total Usage
* total requests
* total tokens
* total cost

## 🔹 2. Cost Over Time
* group by day
* line chart

## 🔹 3. Model Distribution
* usage per model
* pie chart

## 🔹 4. Token Breakdown
* input vs output tokens

## 🔹 5. Recent Activity Feed
* last 20 requests
* show: model, prompt preview, cost, timestamp

## 🔹 6. Top Expensive Requests
* highest cost calls
* useful for debugging

---

# 📊 8.3 Example Aggregation Query

```python
SELECT
    model,
    COUNT(*) as request_count,
    SUM(total_tokens) as tokens,
    SUM(estimated_cost) as cost
FROM requests
GROUP BY model;
```

---

# 🎨 8.4 UI Layout

### Dashboard Page
```
----------------------------------
| Total Cost | Total Requests     |
----------------------------------
| Cost Over Time (Line Chart)     |
----------------------------------
| Model Distribution (Pie Chart)  |
----------------------------------
| Recent Activity Table           |
----------------------------------
```

---

# 🧪 9. Testing Updates (IMPORTANT)

Add tests for:
### Cost Calculation
* [ ] Known model pricing correct
* [ ] Unknown model uses default
* [ ] Zero tokens = zero cost

### Dashboard API
* [ ] `/api/stats` returns correct aggregates
* [ ] Values match DB

---

# ⚠️ Important Design Insight

👉 **Pricing != actual cost**
Real-world cost varies, but this system provides an **estimated cost** sufficient for control and observability.

---

# 🚀 Final Deliverables (Updated)
* Pricing config (`pricing.py`)
* Cost calculation service
* Updated DB schema
* Dashboard UI (Jinja2 or React)
* Aggregation endpoints
* Extended test suite

---

# ⏱️ Estimated Time
* Pricing: 1–2 hours
* Dashboard: 3–5 hours
Total: **~8–12 hours MVP**
