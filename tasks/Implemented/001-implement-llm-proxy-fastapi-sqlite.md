# ✅ Task: Implement LLM Proxy with Logging (FastAPI + SQLite) — *Improved Version*

## 🎯 Objective

Build a lightweight, production-ready proxy server that:

* Intercepts all LLM requests
* Logs structured usage data to SQLite
* Forwards requests to OpenAI transparently

This acts as a **controlled gateway for observability, debugging, and cost tracking**.

---

# 🏗️ Scope (Refined)

## 1. Proxy Server (FastAPI)

### Requirements

* Endpoint:
  ```
  POST /v1/chat/completions
  ```
* Accept **fully OpenAI-compatible payloads**
* Forward request using `httpx.AsyncClient`
* Return **exact upstream response (no mutation)**

### ⚠️ Important

* Preserve headers (especially `Authorization`)
* Support streaming = ❌ (MVP: explicitly out of scope)

---

## 2. Interception Logic (Enhanced)

### Capture BEFORE request

* `model`
* `messages`
* `timestamp`
* `request_id` (generate UUID)

### Capture AFTER response

* `response text`
* `usage`:
  * `prompt_tokens`
  * `completion_tokens`
  * `total_tokens`
* `latency_ms`

---

## 3. Logging Layer (SQLite + Async)

### Database

```
sqlite+aiosqlite:///./ai_usage.db
```

### Why async?

* Prevent blocking FastAPI event loop
* Reduce risk of `database is locked` errors

---

### Table: `requests`

| Column            | Type          |
| ----------------- | ------------- |
| id                | Integer (PK)  |
| request_id        | String (UUID) |
| timestamp         | DateTime      |
| model             | String        |
| prompt            | Text          |
| response          | Text          |
| prompt_tokens     | Integer       |
| completion_tokens | Integer       |
| total_tokens      | Integer       |
| latency_ms        | Integer       |

---

## 4. Database Best Practices (MANDATORY)

* Use `AsyncSession` (not sync session)
* Use FastAPI `Depends()` for session injection
* Ensure:
  * commit on success
  * rollback on failure
  * session always closes

👉 This prevents leaks and ensures data integrity.

---

## 5. Error Handling (NEW — REQUIRED)

* If upstream API fails:
  * Return exact status code + body
  * DO NOT crash server
* Log failed requests with:
  * `response = NULL`
  * error flag (optional field)

---

## 6. Project Structure (ENFORCED)

```
app/
 ├── main.py
 ├── database.py
 ├── models.py
 ├── schemas.py (optional)
 ├── services/
 │    └── proxy.py
 └── tests/
      └── test_proxy.py
```

👉 Separation improves testability and maintainability.

---

## 🧪 Testing & Acceptance Criteria (UPGRADED)

### 🔁 Full Flow Test (MANDATORY)

You must simulate the full lifecycle:

### 1. Mock upstream (OpenAI)

Use:
* `respx` OR `pytest-httpx`

Mock:
```
POST https://api.openai.com/v1/chat/completions
```

Return:
```json
{
  "choices": [{"message": {"content": "Hello"}}],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 7,
    "total_tokens": 12
  }
}
```

---

### 2. Send request to proxy

Use:
```python
httpx.AsyncClient(app=app)
```

---

### 3. Verify forwarding

* Correct URL
* Correct headers
* Payload unchanged

---

### 4. Verify database

Check:
* record exists
* correct:
  * model
  * prompt
  * response
  * tokens

---

### 5. Verify response passthrough

* Response JSON EXACTLY matches mock

---

### 6. Isolation (STRICT)

* Use **separate test DB**
* Clean DB between tests

---

## ✅ Acceptance Criteria Checklist

* [ ] Proxy endpoint works with OpenAI-compatible requests
* [ ] Requests are intercepted and forwarded correctly
* [ ] Response passthrough is exact (no mutation)
* [ ] SQLite logging works reliably
* [ ] Async DB prevents blocking
* [ ] Token counts are accurate
* [ ] Latency is recorded
* [ ] Errors are handled gracefully
* [ ] Pytest suite passes
* [ ] No real API calls required

---

## ⚙️ Tech Stack (Updated)

### Core

* fastapi
* uvicorn
* httpx
* sqlalchemy (async)
* aiosqlite
* python-dotenv

### Testing

* pytest
* pytest-asyncio
* respx

---

## 🚀 Bonus (Optional but High Value)

* Add `/logs` endpoint (basic filtering)
* Add cost estimation (per model pricing)
* Add simple UI dashboard
* Add request size / risk flags

---

## ⚠️ Known Constraints (SQLite)

* Single-writer limitation
* May lock under heavy concurrency

👉 Acceptable for MVP, but not scalable.

---

## 🧠 Key Engineering Insight

This system works because:

```
App → Proxy → LLM
        ↓
     Logging
```

Control over the **network path = full observability**

---

## ⏱️ Estimated Time

* MVP: 4–6 hours
* With tests + polish: 6–10 hours

---

## 📦 Deliverables

* Fully working proxy
* SQLite DB file
* Passing test suite
* Clean, modular codebase

---

# 🔥 Final Notes (Critical Improvements Added)

Compared to original:

* ✅ Async DB (prevents real bugs)
* ✅ Latency tracking
* ✅ Error handling
* ✅ Test isolation
* ✅ Proper architecture
* ✅ SQLite limitations acknowledged
