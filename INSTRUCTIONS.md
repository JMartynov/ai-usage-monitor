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
