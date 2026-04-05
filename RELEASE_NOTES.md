# Release Notes

## v0.1.0 - Initial AI Proxy Implementation
* Migrated MVP tech stack to Python/FastAPI using aiosqlite for database persistence.
* Added a proxy endpoint `/v1/chat/completions` transparently forwarding to OpenAI.
* Integrated SQLAlchemy and Pydantic models for request logs tracking model, tokens, latency, prompt, and response.
* Isolated unit testing strategy configured with `respx` mock upstream testing to ensure robustness and correctness.
