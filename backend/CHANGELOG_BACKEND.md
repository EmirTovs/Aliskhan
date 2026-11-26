# Backend changes — 2026-11-26

## Production job lifecycle

- Added `started_at` to production jobs.
- Added reservation states: `reserved`, `released`, `consumed`.
- Added `POST /api/v1/production-jobs/{id}/start`.
- Added `POST /api/v1/production-jobs/{id}/cancel`.
- Added `POST /api/v1/production-jobs/{id}/complete`.
- Cancellation releases active reservations without deleting their history.
- Completion consumes only the exact batches already reserved for the job, updates batch quantity and reserved quantity, and writes `production_consumption` stock movements.
- Lifecycle operations write audit log entries and run in a single database transaction.
- Job detail now distinguishes active reserved quantities from consumed quantities.
- Fixed production-job pagination arguments (`limit` / `offset`) between API and service.
- Added proper 404 handling for missing jobs.

## Migration

Run from the backend directory after configuring the project `.env`:

```bash
alembic upgrade head
```

The migration is additive and preserves existing production jobs and reservations. Existing reservation rows receive status `reserved`.

## New endpoints

- `POST /api/v1/production-jobs/{job_id}/start`
- `POST /api/v1/production-jobs/{job_id}/cancel`
- `POST /api/v1/production-jobs/{job_id}/complete`

Write access: `technologist`, `manager`. Read access remains `warehouse`, `technologist`, `manager`.
