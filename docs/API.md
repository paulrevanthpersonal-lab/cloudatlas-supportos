# API Reference

The running application publishes interactive documentation at `/docs`.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/api/cases` | Prioritized incident queue |
| `GET` | `/api/cases/{id}` | Case detail with evidence timeline |
| `POST` | `/api/cases` | Create a validated support case |
| `PATCH` | `/api/cases/{id}` | Record status and resolution evidence |
| `POST` | `/api/cases/{id}/events` | Append a typed operational evidence event |
| `GET` | `/api/metrics` | Aggregate command-center metrics |
| `GET` | `/api/events` | Recent evidence timeline |
| `GET` | `/api/runbooks` | Search the 18-runbook procedure library |

Example:

```bash
curl -X POST http://localhost:8000/api/cases \
  -H 'Content-Type: application/json' \
  -d '{"title":"VPN authentication failure","service":"Remote Access","owner":"Paul R.","priority":"high","impact":"Remote engineers cannot connect"}'
```

`GET /api/cases` accepts `query`, `status`, and `priority` filters. `GET /api/runbooks` accepts `query`. The generated OpenAPI page remains the source of truth for request schemas and response validation.
