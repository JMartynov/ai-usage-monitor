# Instructions

## Run Dev Server
You can run the FastAPI server locally by executing:
```bash
uvicorn app.main:app --reload
```
By default, the server listens on `http://127.0.0.1:8000`.
Proxy endpoints are exposed for interacting with OpenAI.
The Dashboard is available at `http://127.0.0.1:8000/dashboard`.

## Database
The system uses SQLite via `aiosqlite`. Ensure you provide a `DATABASE_URL` environment variable if you want to use a specific file. By default, it uses `sqlite+aiosqlite:///./ai_usage.db`.

## Tests
Testing runs via `pytest`. Use the standard command to verify functionality:
```bash
pytest app/tests/
```
Tests automatically use an in-memory SQLite schema properly isolated per run.

To run end-to-end acceptance tests:
```bash
python scripts/test_acceptance.py
```
Tests run automatically via GitHub Actions CI pipeline.

## Linter
Run linting with:
```bash
flake8 app/
```

## Dashboard & Pricing
The new Dashboard and Pricing Engine are now fully integrated. The Dashboard aggregates data such as total usage, cost over time, model distribution, token breakdown, and provides a recent activity feed and top expensive requests view.

## Alerting Engine
The Active Alerting System evaluates proxy logs for potential budget overruns and cost/token anomalies. Thresholds are configured inside `app/config/alerts.py`. It integrates with Guardrails to automatically enforce model downgrades and cut off usage on breached budgets.

## Updates
* Ensure you regularly run `scripts/test_acceptance.py` to test the E2E flow including `/api/alerts` and the Active Alerting functionality validation!
