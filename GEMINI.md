# GEMINI.md — AI Usage Monitor (ai-usage)

This file gives AI coding agents the context they need to work safely and effectively in this repository.

## Agent TL;DR
- **Focus on Proxy Performance.** The proxy layer should add minimal latency to LLM requests.
- **Maintain API Compatibility.** The proxy must be a drop-in replacement for standard LLM provider APIs (e.g., OpenAI, Anthropic).
- **Verify with Integration Tests.** Always verify proxy forwarding and logging with real or mocked LLM API calls.
- **Secure Credentials.** Never log or store raw API keys. Use environment variables for provider keys.

## 🏗️ Core Philosophy & Architecture
- **Proxy Layer**: An Express-based middleware that intercepts, logs, and forwards requests.
- **Observability First**: Tracking token usage, costs, and request/response metadata is the primary goal.
- **Minimalist Dashboard**: A React-based UI for visualizing usage trends and costs.
- **Data Persistence**: Uses a relational schema (SQLite for MVP, PostgreSQL for production) to store logs.

## 🛡️ Mandatory Workflows & Mandates

### 🌐 Global Obligatory Steps (Every Task)
Before concluding any task, you MUST:
0.  **Linting**: Run `npm run lint` to ensure code quality and adherence to style guides.
1.  **Agentic Review**: Perform a self-review of your changes using `git diff`. Analyze the architecture, logic, and style. Fix any issues identified during this review before proceeding.
2.  **Add tests**: Add unit tests for logic and integration tests for proxy/API endpoints if feature/fix implemented.
3.  **Add acceptance tests**: If a new major feature is implemented, you MUST add or update automated end-to-end (E2E) acceptance tests. These tests must install/run the project from a clean state, simulate a real-life scenario (e.g., sending traffic through the proxy, generating an alert), and formally validate the outcome.
4.  **Test Validation**: Run `npm test` and ensure ALL tests pass. Never suggest a change that breaks the existing suite.
5.  **Documentation**: Update `README.md` to reflect changes in architecture, API endpoints, or environment variables.
6.  **Manual Verification**: Verify proxy behavior using `curl` or a test script to ensure requests are correctly forwarded and logged.

### 🛠️ Working Principles
- **Incremental Progress**: Work in small, understandable steps. After each change, verify results and adjust if necessary.
- **Strict Scope**: Do NOT make unrelated changes to the code, even if you identify potential improvements. Stay focused on the current task.
- **Proactive Suggestions**: If you identify opportunities for improvement outside of the current task, suggest them to the user instead of implementing them directly.
- **Token Efficiency**: Prefer `tail` or scoped reads/searches for large outputs to maintain context efficiency.

### 1. Modifying the Proxy
- **Compatibility**: Ensure any changes to the proxy do not break the OpenAI/Anthropic API contract.
- **Error Handling**: Implement robust error handling for upstream API failures (e.g., rate limits, timeouts).
- **Logging**: Ensure all relevant metadata (model, tokens, cost) is captured before forwarding.

### 2. Modifying the Database Schema
- **Migrations**: Use a migration tool (e.g., Knex or Prisma) if a migration path is established.
- **Schema Integrity**: Ensure timestamps and total token counts are always accurate.

### 3. Modifying the Dashboard
- **Responsive Design**: Ensure the dashboard remains usable on different screen sizes.
- **Data Visualization**: Use standard libraries (e.g., Chart.js or Recharts) for usage charts.

## 🧪 Testing Guidelines
1. **Unit Tests**: Test core logic (e.g., cost calculation, token estimation).
2. **Integration Tests**: Test proxy forwarding to mocked upstream APIs.
3. **E2E Tests**: Test the full flow from Client App -> Proxy -> Database -> Dashboard.
4. **Mocking**: Use `nock` or similar libraries to mock LLM provider responses.

## ⚙️ Tooling & Maintenance
- **Development**: `npm run dev` to start both proxy and dashboard in development mode.
- **Build**: `npm run build` to prepare for production.
- **Database**: Tools for inspecting the SQLite database (e.g., `sqlite3`).

## ⚠️ Sensitive Areas
- **Proxy Middleware**: Core logic for interception. Small bugs here can break all forwarded requests.
- **Credential Handling**: Ensure provider API keys are never leaked in logs or dashboard.
- **Cost Calculation**: Financial data must be accurate; verify cost multipliers for different models.
