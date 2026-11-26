# CandleFlow AI — Frontend

React + TypeScript + Vite frontend for CandleFlow AI backend.

## Requirements
- Node.js 20+
- Backend API available at `http://127.0.0.1:8000`

## Run locally
```bash
npm ci
cp .env.example .env
npm run dev
```

Open `http://localhost:5173`.

## Environment
Set `VITE_API_URL` in `.env` (frontend root):
```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
```
Never put the OpenAI API key or other backend secrets in frontend environment variables.

## Architecture
- `src/app` — application shell and navigation
- `src/components/ui` — shared UI primitives
- `src/components/layout` — layout component area
- `src/features/*` — feature-oriented pages and feature logic
- `src/shared/api` — shared HTTP client and API types
- `src/shared/types` — shared domain/navigation types
- `src/styles.css` — global design system and responsive styles

Feature modules: auth, dashboard, materials, suppliers, batches, recipes, production, assistant.

## Build
```bash
npm run build
```

The build runs TypeScript validation followed by Vite production bundling.
