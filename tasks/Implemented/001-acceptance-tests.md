# 🧪 Task: End-to-End Acceptance Testing

## 🎯 Objective

Create an automated end-to-end (E2E) acceptance test suite that validates the full lifecycle of the AI Usage Monitor from a clean slate. This proves the system works exactly as a user would experience it.

---

# 🏗️ 1. Scope of the Acceptance Test

The acceptance test must simulate a real-world user installing, running, and using the project. It should be a standalone script (e.g., a `bash` script or a Python script `scripts/acceptance_test.py` using `subprocess`) that runs end-to-end outside the standard unit test suite.

## 🔹 1.1 Setup Phase
* Create a clean test environment (e.g., temporary directory for DB).
* Install dependencies via `pip install -r requirements.txt`.
* Initialize a temporary SQLite database (using a unique `DATABASE_URL` like `sqlite+aiosqlite:///./test_acceptance.db`).
* Start the FastAPI proxy server in the background (using `uvicorn`).
* Poll the server until it is ready (e.g., expecting a 200 OK on `/dashboard`).

---

## 🔹 1.2 Execution Phase (Real-life Scenario)
* **Mock Upstream:** Spin up a lightweight mock upstream server to simulate the OpenAI API (so we don't spend real money or hit rate limits during tests). Point the proxy to this mock server.
* **Simulate Traffic:** Send multiple LLM requests through the proxy:
  * Mix of different models (e.g., `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`).
  * Normal requests with standard token usage.
  * A "runaway" high-cost request (huge token count) to test the anomaly/budget alerts.
  * An invalid request to ensure upstream errors (e.g., 400/500) are handled gracefully and logged.

---

## 🔹 1.3 Validation Phase
* **Database State**: Directly query the temporary SQLite database to verify:
  * Requests were logged.
  * Tokens were recorded accurately based on the mock responses.
  * Costs were calculated correctly according to `MODEL_PRICING`.
* **Dashboard API**: Make a `GET` request to the `/api/stats` endpoint and verify the JSON response contains the expected aggregated values (total cost, token counts, model distribution).
* **Alerts Validation**: Query the `/alerts` endpoint (or DB) to ensure the high-cost request triggered the appropriate anomaly/budget alerts.

---

## 🔹 1.4 Teardown Phase
* Gracefully shut down the background FastAPI proxy server and the mock upstream server.
* Clean up the temporary SQLite database file.
* Exit with code `0` on success, or print detailed logs and exit with `1` on failure.

---

# ⚙️ 2. Implementation Details

Create an executable script at:
`scripts/run_acceptance.sh` or `scripts/test_acceptance.py`

### Checklist
* [ ] Script successfully spins up the app and a mock upstream server.
* [ ] Script successfully routes traffic through the proxy.
* [ ] Script validates the dashboard metrics match the traffic sent.
* [ ] Script validates an alert was generated for an anomalous request.
* [ ] Script tears down all processes, even if a test assertion fails.

---

# ⏱️ 3. Estimated Time
* Test scaffolding (startup/teardown logic): 1-2 hours
* Scenario simulation (mocking upstream, sending requests): 1-2 hours
* Assertions and validations: 1 hour

Total: **~3-5 hours**
