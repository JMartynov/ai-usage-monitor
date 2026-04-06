# Release Notes

## [Unreleased]
- **CI**: Added GitHub Actions Continuous Integration pipeline `.github/workflows/ci.yml` that runs linting, unit tests, and acceptance tests on pushes and PRs to main.
- **Tests**: Added End-to-End Acceptance test script in `scripts/test_acceptance.py` to simulate a real-world user setting up and running traffic.
- **Features**: Added `/api/alerts` endpoint for anomaly/budget alerts checking based on high token or high cost thresholds.
- **Requirements**: Added `flake8` to `requirements.txt`.

## v0.2.0 - Pricing Engine & Dashboard
* Added `app/config/pricing.py` to support dynamic price configurations for different models.
* Added `app/services/pricing.py` to accurately calculate request cost based on prompt and completion tokens.
* Extended database schema in `app/models.py` to store estimated cost per request.
* Implemented the Dashboard UI available at `/dashboard` using Jinja2 Templates and Chart.js.
* Added `/api/stats` endpoint for retrieving aggregations on cost, tokens, and model distribution.
* Extended `pytest` suite for new endpoint and proxy integrations.

## v0.1.0 - Initial AI Proxy Implementation
* Migrated MVP tech stack to Python/FastAPI using aiosqlite for database persistence.
* Added a proxy endpoint `/v1/chat/completions` transparently forwarding to OpenAI.
* Integrated SQLAlchemy and Pydantic models for request logs tracking model, tokens, latency, prompt, and response.
* Isolated unit testing strategy configured with `respx` mock upstream testing to ensure robustness and correctness.
