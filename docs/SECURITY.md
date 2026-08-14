# Security Model

This repository is a portfolio demonstration, not a production ticketing system.

## Implemented controls

- Typed input validation and bounded field lengths
- Parameterized SQL queries
- Non-root container runtime
- Minimal GitHub Actions permissions
- No secrets or credentials in the repository
- HTML escaping for API-provided content

## Production requirements

Add OIDC authentication, role-based authorization, audit retention controls, TLS termination, secret management, CSRF protection for cookie-based sessions, rate limits, encrypted backups, dependency scanning, and centralized security logging before handling real support data.

