# Interview guide

## One-minute explanation

CloudAtlas SupportOS is a small incident-operations platform built to make support work auditable. It combines structured incident intake, severity and SLA tracking, diagnostic evidence, timeline events, and explicit recovery verification in one workflow.

## Decisions I can explain

- I used FastAPI for typed request validation and automatic API documentation.
- I chose SQLite to keep the demonstration reproducible while preserving a clean migration path to PostgreSQL.
- The service separates API models, persistence, and the browser client so each part can evolve independently.
- Recovery is represented as evidence and events rather than a single opaque status field.
- The interface prioritizes severity, ownership, SLA exposure, and next action over decorative analytics.

## Trade-offs

SQLite is excellent for a single-node portfolio deployment but is not the right write-scaling choice for a multi-region production service. Authentication is intentionally outside this local demonstration; a real deployment would place the API behind an identity-aware gateway and persist actor identity in every audit event.

## Next production steps

1. Add OpenID Connect and role-scoped permissions.
2. Replace SQLite with PostgreSQL and migrations.
3. Send traces and service-level indicators to an observability backend.
4. Add background SLA notifications and escalation policies.
5. Exercise disaster recovery and data-retention procedures.
