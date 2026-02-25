# Databricks Apps Authorization — Reference Guide

> Source: [Microsoft Learn — Configure authorization in a Databricks app](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth)
> Fetched: 2026-02-25

PM Hub uses **user authorization (OBO)** for all data queries.
The app may also use **app authorization (service principal)** for system
operations like logging and shared config. Both models can coexist.

## Two Authorization Models

### App Authorization (Service Principal)

Every Databricks App gets an auto-provisioned service principal. It acts
as the app's own identity — shared across all users.

- **Use for**: Background tasks, logging, shared config, external services
- **NOT for**: Data queries that should respect per-user UC permissions
- **Credentials**: Auto-injected as environment variables:
  - `DATABRICKS_CLIENT_ID` — OAuth client ID
  - `DATABRICKS_CLIENT_SECRET` — OAuth client secret
- The Databricks SDK auto-detects these via unified auth (`Config()`)

```python
# App authorization — service principal identity
from databricks import sql
from databricks.sdk.core import Config

cfg = Config()  # Uses DATABRICKS_CLIENT_ID/SECRET automatically

conn = sql.connect(
    server_hostname=cfg.host,
    http_path="<warehouse-http-path>",
    credentials_provider=lambda: cfg.authenticate,  # service principal
)
```

**PM Hub rule**: This pattern is acceptable ONLY for system-level operations
(audit logging, app config). Never use it for user-facing data queries.

### User Authorization (OBO — On-Behalf-Of)

The app acts with the identity of the logged-in user. The user's OAuth
access token is forwarded to the app via HTTP headers.

- **Use for**: All data queries, any operation that should respect UC permissions
- **Enables**: Row-level filters, column masks, per-user audit trails
- **Prerequisite**: Workspace admin must enable user authorization (Public Preview)
- **Credentials**: From `X-Forwarded-Access-Token` HTTP header

```python
# User authorization — per-user identity (PM Hub approved pattern)
from databricks import sql
from databricks.sdk.core import Config
from flask import request

cfg = Config()
user_token = request.headers.get("x-forwarded-access-token")

conn = sql.connect(
    server_hostname=cfg.host,
    http_path="<warehouse-http-path>",
    access_token=user_token,  # user's own token
)
```

**PM Hub rule**: This is the REQUIRED pattern for all data queries.

## Prerequisites for User Authorization

1. **Workspace admin must enable user authorization** — it's a Public Preview feature
2. **App must declare OAuth scopes** — at minimum `sql` for SQL warehouse queries
3. **User must grant consent** on first access (or admin grants consent on behalf)
4. **Existing apps must be restarted** after enabling user authorization

### Required OAuth Scopes for PM Hub

| Scope | Purpose |
|-------|---------|
| `sql` | Query SQL warehouses on behalf of users |
| `iam.access-control:read` | Read access control (default) |
| `iam.current-user:read` | Read current user identity (default) |

If no scopes are configured, only the two `iam.*` defaults are granted —
these do NOT include data access. The `sql` scope must be explicitly added.

**Scopes enforce least privilege**: Even if a user has full UC permissions,
the app can only exercise permissions within its declared scopes. If the app
only has the `sql` scope, it cannot access model serving endpoints.

## HTTP Headers Available in Databricks Apps

### Always Available (No OBO Required)

| Header | Description |
|--------|-------------|
| `X-Forwarded-Email` | User's email from IdP |
| `X-Forwarded-Preferred-Username` | User's display name from IdP |
| `X-Forwarded-User` | User identifier from IdP |
| `X-Real-Ip` | Client's IP address |
| `X-Forwarded-Host` | Original requested host/domain |
| `X-Request-Id` | UUID for the request |

### Requires User Authorization Enabled

| Header | Description |
|--------|-------------|
| `X-Forwarded-Access-Token` | User's OAuth token for OBO queries |

**Critical**: If user authorization is NOT enabled, `X-Forwarded-Access-Token`
will not be present. The app must handle this gracefully (fall back to sample
data in local dev, show error in production).

## Retrieving Headers in Dash/Flask

```python
from flask import request

# User identity (always available)
email = request.headers.get("x-forwarded-email")
username = request.headers.get("x-forwarded-preferred-username")
user_id = request.headers.get("x-forwarded-user")

# OBO token (requires user authorization enabled)
user_token = request.headers.get("x-forwarded-access-token")
```

**Note**: Headers are lowercase in Flask (`x-forwarded-access-token`).
The lookup is case-insensitive, but be consistent.

## Combining Both Models

PM Hub should use both models:

| Operation | Auth Model | Why |
|-----------|-----------|-----|
| Data queries (SELECT) | **User authorization** | Respect UC permissions, row filters, column masks |
| Data writes (INSERT/UPDATE) | **User authorization** | Audit trail shows real user |
| Audit logging (app_audit_log) | **App authorization** | System-level, not user-specific |
| App configuration reads | **App authorization** | Shared config, not user-specific |
| Background tasks | **App authorization** | No user context available |

## Security Best Practices (from Microsoft)

1. **Never log, print, or write tokens** — not in logs, debug output, or error handlers
2. **Request minimum scopes** — only `sql` and defaults for PM Hub
3. **Store app code in restricted folders** — only trusted users can modify
4. **Grant `CAN MANAGE` only to trusted developers** — `CAN USE` for end users
5. **Peer review all app code** before production deployment
6. **Log structured audit records** for every action on behalf of users
7. **Use dedicated service principals** — never share across apps
8. **Rotate service principal credentials** when app creators leave

## Review Agent Checks

When reviewing PM Hub code for auth compliance:

- [ ] All data queries use `access_token=user_token` (user authorization)
- [ ] User token sourced from `request.headers.get("x-forwarded-access-token")`
- [ ] Token validated before use (None check → sample data fallback)
- [ ] `credentials_provider` only used for system operations, never data queries
- [ ] No tokens logged, printed, or written to files
- [ ] No hardcoded tokens anywhere
- [ ] `app.yaml` uses `valueFrom` for secrets, not `value` with sensitive data
- [ ] Service principal credentials not shared across apps
