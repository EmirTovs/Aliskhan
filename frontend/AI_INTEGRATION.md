# AI assistant integration

The assistant page uses the backend routes below and does not call OpenAI directly from the browser:

- `GET /ai/conversations`
- `GET /ai/conversations/{conversation_id}/messages`
- `DELETE /ai/conversations/{conversation_id}` (available in API; UI deletion can be added separately)
- `POST /ai/chat/stream` (SSE)
- `POST /ai/confirm-production-plan`

The access token is read from the frontend session and sent as a Bearer token. The OpenAI API key must remain in the backend environment only.
