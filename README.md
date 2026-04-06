# AI Usage Monitor (ai-usage)

A very simple analytics tool for tracking Large Language Model (LLM) usage across your applications.

## 🚀 Overview

AI Usage Monitor is a lightweight proxy + dashboard system that helps you understand how your AI is being used.

It tracks:

* Which models are used
* Token consumption
* Estimated costs
* Prompts and responses
* Potential risks (basic flagging)

Built as an MVP, it is intentionally simple, fast to deploy, and easy to extend.

---

## 🎯 Problem

When using LLM APIs (OpenAI, Anthropic, etc.), teams often lack visibility into:

* Who is using which model
* How much it costs
* What prompts are being sent
* Whether there are risky or sensitive inputs

This leads to:

* Unexpected costs
* Lack of governance
* Poor debugging visibility

---

## 💡 Solution

AI Usage Monitor acts as a **proxy layer** between your app and LLM providers.

It logs requests and provides a simple dashboard for analysis.

---

## 🧱 Architecture

```
Client App → Proxy Server → LLM API
                     ↓
                 Database
                     ↓
                 Dashboard
```

### Components

1. **Proxy Server**

   * Intercepts all LLM requests
   * Logs metadata
   * Forwards request to provider

2. **Database**

   * Stores usage logs
   * Simple schema (requests, tokens, cost)

3. **Dashboard**

   * Displays analytics
   * Basic filtering and charts

---

## 📊 Features (MVP)

### Tracking

* Model usage (GPT-4, Claude, etc.)
* Tokens (input/output)
* Cost estimation
* Request timestamps

### Prompt Logging

* Store prompts
* Store responses
* Search & filter

### Risk Signals (Basic)

* Long prompts
* Repeated prompts
* Potential sensitive keywords (configurable)

### Dashboard (New!)

* Total usage
* Cost overview (Line Chart)
* Model distribution (Pie Chart)
* Token breakdown (Doughnut Chart)
* Recent activity feed
* Top expensive requests
* Anomalies & Budget alerts (via `/api/alerts`)

### Pricing Engine (New!)

* `estimated_cost` tracking per request.
* Support for variable input/output token pricing per model.
* Fallback to default pricing for unknown models.

---

## 🛠️ Tech Stack (Suggested)

* **Backend**: Python (FastAPI)
* **Database**: SQLite (via aiosqlite for MVP)
* **Frontend**: Jinja2 Templates + Chart.js for dashboard UI
* **Auth (optional)**: Basic API keys

---

## ⚡ Quick Start

### 1. Clone repo

```bash
git clone https://github.com/yourname/ai-usage.git
cd ai-usage
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create `.env`:

```env
DATABASE_URL=sqlite+aiosqlite:///./ai_usage.db
```

### 4. Run server

```bash
uvicorn app.main:app --reload
```

### 5. Point your app to proxy

Instead of calling OpenAI directly:

```
https://api.openai.com/v1/chat/completions
```

Use:

```
http://localhost:8000/v1/chat/completions
```

### 6. View the Dashboard

Open your browser to:

```
http://localhost:8000/dashboard
```

---

## 📦 API Design (Example)

### Proxy Endpoint

`POST /v1/chat/completions`

* Accepts standard OpenAI-compatible payload
* Logs request
* Forwards to provider
* Returns response

---

## 🗄️ Data Model (Simplified)

### requests

* id
* timestamp
* model
* prompt_tokens
* completion_tokens
* total_tokens
* estimated_cost
* prompt
* response
* user_id (optional)

---

## 🔄 Continuous Integration

We use GitHub Actions to automate our testing pipeline. Any push or pull request to the `main` branch will trigger:

1. **Linting** with `flake8` to enforce style and syntax.
2. **Unit and Integration Tests** with `pytest`.
3. **Acceptance Tests** using a standalone script that spins up the app and a mock server to validate e2e usage.

## 📈 Future Improvements

* Per-user analytics
* Rate limiting
* Budget alerts
* Team dashboards
* Role-based access
* Multi-provider support
* Real-time streaming logs
* Advanced risk detection (PII, jailbreaks)

---

## 💰 Monetization Idea

* Free: basic dashboard
* Paid:

  * team features
  * alerts
  * advanced analytics

---

## 🧪 Why This Works

* Extremely easy to build
* Immediate value for any AI product
* Growing demand for AI observability

---

## ⚠️ Limitations (MVP)

* Not production-hardened
* Basic risk detection only
* No deep security guarantees

---

## 📄 License

MIT

---

## 🙌 Contributing

PRs welcome. Keep it simple.

---

## 🧭 Summary

AI Usage Monitor is a small but powerful tool to bring visibility into LLM usage with minimal effort.

**Build fast. Ship fast. Iterate.**
