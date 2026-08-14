# API Reference

The running application publishes interactive documentation at `/docs`.

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/api/cases` | Prioritized incident queue |
| `POST` | `/api/cases` | Create a validated support case |
| `PATCH` | `/api/cases/{id}` | Record status and resolution evidence |
| `GET` | `/api/metrics` | Aggregate command-center metrics |
| `GET` | `/api/events` | Recent evidence timeline |

Example:

```bash
curl -X POST http://localhost:8000/api/cases \
  -H 'Content-Type: application/json' \
  -d '{"title":"VPN authentication failure","service":"Remote Access","owner":"Paul R.","priority":"high","impact":"Remote engineers cannot connect"}'
```

