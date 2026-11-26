# CandleFlow AI integration

## Configuration
Copy `.env.example` to the project root `.env` (the directory containing `backend/` and `frontend/`). Set `OPENAI_API_KEY` there. Keep the key on the backend only; do not use a `VITE_` prefix and do not commit `.env`.

The model defaults are `gpt-5` and `gpt-5-mini`; change them to model IDs enabled for your OpenAI API project if needed. ChatGPT subscription billing and API billing are separate.

## Migration
From the backend directory with the project virtualenv active:

```bash
alembic upgrade head
```

## Start
```bash
uvicorn app.main:app --reload
```

AI endpoints are under `/api/v1/ai` and require the existing bearer-token authentication:
- `GET /conversations`
- `GET /conversations/{id}/messages`
- `DELETE /conversations/{id}`
- `POST /chat/stream` (SSE response envelope)
- `POST /confirm-production-plan` (technologist/manager only)

The assistant exposes read-only stock, production deficit, batch history and job-cost tools, a proposal-only production planning tool, and the Responses API Code Interpreter. A production plan is not committed until the user confirms it through `/confirm-production-plan`.

## Current implementation boundary
The endpoint uses Server-Sent Events, but this first integration currently emits the completed assistant result as one SSE event rather than token-by-token deltas. Code Interpreter execution is enabled, but downloadable artifact handling and a UI artifact gallery are not included yet. Label-service retries, personal memory controls, PII pseudonymization, and the full golden-question evaluation suite remain separate follow-up work.
