# Operations Runbook

## Start

1. Install the project dependencies.
2. Start Uvicorn or Docker Compose.
3. Confirm `/health` returns `status: ok`.
4. Open the dashboard and confirm seeded cases load.

## Investigate an unhealthy service

1. Review application logs and the container health check.
2. Confirm the data directory is writable.
3. Run `python -m pytest` to separate runtime configuration from application defects.
4. Back up `data/cloudatlas.db` before database repair.

## Recovery

The SQLite store is recreated and seeded when no database exists. For a demo reset, stop the service, remove the database, and restart. Never use that reset procedure on a production datastore.

