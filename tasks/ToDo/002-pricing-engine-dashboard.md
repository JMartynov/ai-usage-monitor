# 🚀 Task Extension: Pricing Engine + Dashboard (Single User)

---

# 📚 Core Concepts & Prerequisites

Before starting the implementation, familiarize yourself with these key concepts:

1. **Token Pricing Model**: LLM providers (like OpenAI) charge differently for input (`prompt_tokens`) and output (`completion_tokens`). Output tokens are more expensive. While official docs often list prices per 1M tokens, we will configure our system using per-1K rates for simplicity.
2. **Reasoning Tokens**: Some modern models (like `o1` or `o3-mini`) consume "hidden" reasoning tokens that count towards completion tokens. Our cost calculator relies strictly on the `usage` block returned by the API.
3. **Async SQLAlchemy Aggregation**: Querying stats in an async environment requires `sqlalchemy.ext.asyncio.AsyncSession`. You will use `await db.execute(select(...))` combined with SQL functions like `sqlalchemy.func.sum` and `sqlalchemy.func.count`.
4. **Server-Side Rendering (SSR) vs SPA**: For this MVP, we use SSR with FastAPI's `Jinja2Templates` to serve the initial HTML, and a separate `/api/stats` endpoint that the frontend (Vanilla JS) calls to populate `Chart.js` graphs.

---

# 💰 7. Model Pricing Configuration (NEW — REQUIRED)

## 🎯 Objective

Enable **accurate cost estimation per request** based on model and token usage.

---

## 📊 Background

LLM APIs are priced per token (input + output), and **output tokens are usually significantly more expensive than input tokens** ([OpenAI Platform][1])

---

## 🧱 Implementation Details

### 7.1 Pricing Config (Static Table)

Create a config file to centralize pricing constants:

`app/config/pricing.py`

**Implementation details**:
* Use a nested dictionary mapping model identifiers (e.g., `gpt-4o`) to their respective `input_per_1k` and `output_per_1k` costs.
* Ensure prices are up to date and derived from official pricing (converted from per-1M tokens to per-1k).

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

### 7.2 Default Pricing (MANDATORY)

Handle unknown models gracefully to avoid crashes when new models are used:

```python
DEFAULT_PRICING = {
    "input_per_1k": 0.002,
    "output_per_1k": 0.008
}
```

---

### 7.3 Cost Calculation Function

`app/services/pricing.py`

**Implementation details**:
* The function should accept `model` (str), `prompt_tokens` (int), and `completion_tokens` (int).
* It must gracefully handle `None` values (e.g., if a request failed and returned no tokens) by defaulting them to `0`.
* Calculate input and output cost separately, sum them, and round to 6 decimal places to prevent floating-point precision issues.

```python
def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    # Handle None cases
    prompt_tokens = prompt_tokens or 0
    completion_tokens = completion_tokens or 0
    
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)

    input_cost = (prompt_tokens / 1000) * pricing["input_per_1k"]
    output_cost = (completion_tokens / 1000) * pricing["output_per_1k"]

    return round(input_cost + output_cost, 6)
```

---

### 7.4 Database Schema Update

`app/models.py`

Add the `estimated_cost` column to the `RequestLog` model. 

| Column         | Type                     | Nullable |
| -------------- | ------------------------ | -------- |
| estimated_cost | `sqlalchemy.Float`       | True     |

*Note: Since SQLite MVP might recreate the DB on startup or use basic schemas, you may not need complex Alembic migrations yet. If modifying an existing DB, ensure you alter the table.*

---

### 7.5 Logging Integration

`app/services/proxy.py`

During response handling, invoke the calculator using the parsed `usage` block from the upstream response:

```python
cost = None
if prompt_tokens is not None and completion_tokens is not None:
    cost = calculate_cost(model, prompt_tokens, completion_tokens)
```

Store this `cost` into the DB.

---

# 📊 8. Dashboard (Single User — Comprehensive MVP)

## 🎯 Objective

Provide **clear visibility into usage, cost, and behavior** using a unified interface.

---

## 🧱 Architecture Options

### Option A (Recommended MVP)

* **Backend**: FastAPI
* **Templating**: `Jinja2Templates`
* **Frontend**: Vanilla HTML/JS with CDN-imported `Chart.js` for graphs

### Option B

* Separate React frontend (Out of scope for initial fast MVP)

👉 Start with **Option A** (faster)

---

# 📈 8.1 Dashboard Endpoints

`app/routers/dashboard.py`

### `GET /dashboard`
* Returns the HTML page (`TemplateResponse`).

### `GET /api/stats`
* Returns JSON containing all aggregated data necessary for the UI to render charts and tables.

---

# 📊 8.2 Metrics & SQLAlchemy Implementation

When building `/api/stats`, you must query the database asynchronously.

## 🔹 1. Total Usage
* Total requests: `select(func.count(RequestLog.id))`
* Total tokens: `select(func.sum(RequestLog.total_tokens))`
* Total cost: `select(func.sum(RequestLog.estimated_cost))`

## 🔹 2. Cost Over Time (Line Chart)
* Group by day using `func.date(RequestLog.timestamp)`.
* Order chronologically.

## 🔹 3. Model Distribution (Pie Chart)
* Group by `RequestLog.model`.
* Return count, token sum, and cost sum per model.

## 🔹 4. Token Breakdown (Doughnut Chart)
* Sum of `prompt_tokens` vs sum of `completion_tokens`.

## 🔹 5. Recent Activity Feed
* Fetch the latest 20 requests: `order_by(desc(RequestLog.timestamp)).limit(20)`.
* Show: model, prompt preview (truncated to ~100 chars), cost, timestamp.

## 🔹 6. Top Expensive Requests
* Fetch top 10 highest cost calls: `order_by(desc(RequestLog.estimated_cost)).limit(10)`.

---

# 🎨 8.4 UI Layout Strategy

The frontend should be a single `dashboard.html` file in `app/templates/`.

### Structure:
1. **Header**: "AI Usage Dashboard"
2. **Summary Cards**: Flexbox row containing Total Requests, Total Tokens, Total Cost.
3. **Charts Row**: Flexbox row with `<canvas>` elements for Cost Over Time, Model Distribution, and Token Breakdown.
4. **Tables Row**: Flexbox row with two tables: Recent Activity and Top Expensive Requests.

### Data Fetching:
Use a `fetch('/api/stats')` call in a `<script>` tag at the bottom of the HTML to retrieve the data, populate the DOM elements, and initialize the Chart.js instances.

---

# 🧪 9. Testing Updates (IMPORTANT)

Add robust test coverage in `app/tests/`.

### Cost Calculation (`test_pricing.py`)
* [ ] **Known model**: Ensure math matches exactly (e.g., `gpt-4o` with 1000 in / 1000 out).
* [ ] **Unknown model**: Ensure it falls back to `DEFAULT_PRICING`.
* [ ] **Zero / None tokens**: Ensure cost returns `0.0` gracefully.

### Dashboard API (`test_dashboard.py`)
* [ ] **Endpoint `/dashboard`**: Returns 200 OK and contains HTML.
* [ ] **Endpoint `/api/stats`**: Returns correct JSON structure.
* [ ] **Data accuracy**: Seed the test DB with known requests and ensure aggregates (sum, count) match expected values.

---

# ⚠️ Important Design Insight

👉 **Pricing != actual cost**

Real-world cost varies because:

* Token usage differs per request.
* Models may consume hidden reasoning tokens ([arXiv][2]).
* Prices change over time (MVP does not version historical prices).

Your system provides:
✅ **Estimated cost (sufficient for operational control and observability)**

---

# 🚀 Final Deliverables (Updated)

1. `app/config/pricing.py` (Constants)
2. `app/services/pricing.py` (Logic)
3. `app/models.py` (Added `estimated_cost` column)
4. `app/routers/dashboard.py` (Endpoints)
5. `app/templates/dashboard.html` (UI)
6. `app/tests/test_pricing.py` & `app/tests/test_dashboard.py` (Tests)

---

# 🧠 Key Upgrade

Before:
→ Passive Logging tool

After:
→ **LLM Observability Platform**

* Cost tracking ✅
* Usage analytics ✅
* Optimization insights ✅

---

# ⏱️ Updated Time Estimate

* Pricing logic & DB: 1–2 hours
* Dashboard API & UI: 3–5 hours
* Testing & Polish: 2-3 hours

Total: **~6–10 hours MVP**

---

[1]: https://platform.openai.com/docs/pricing/?utm_source=chatgpt.com "Pricing | OpenAI API"
[2]: https://arxiv.org/abs/2603.23971?utm_source=chatgpt.com "The Price Reversal Phenomenon: When Cheaper Reasoning Models End Up Costing More"