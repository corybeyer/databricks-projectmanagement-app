# Layer Rules — PM Hub Architecture

## Layer Diagram

```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│  pages/ + components/ + callbacks/      │
│  - Dash layouts, callbacks, UI logic    │
│  - May import: services, components     │
│  - Must NOT import: repositories, db    │
└────────────────┬────────────────────────┘
                 │ calls
                 ▼
┌─────────────────────────────────────────┐
│           SERVICE LAYER                 │
│  services/                              │
│  - Business logic, validation, auth     │
│  - May import: repositories, config     │
│  - Must NOT import: pages, components,  │
│    callbacks, dash                      │
└────────────────┬────────────────────────┘
                 │ calls
                 ▼
┌─────────────────────────────────────────┐
│         REPOSITORY LAYER                │
│  repositories/ (or utils/data_access)   │
│  - Database queries, data mapping       │
│  - May import: db, config, models       │
│  - Must NOT import: services, pages     │
└────────────────┬────────────────────────┘
                 │ calls
                 ▼
┌─────────────────────────────────────────┐
│       INFRASTRUCTURE LAYER              │
│  config/ + db/                          │
│  - Connections, config, caching         │
│  - May import: stdlib, third-party only │
│  - Must NOT import: any app layer       │
└─────────────────────────────────────────┘
```

## Import Matrix

| From ↓ / To → | pages | components | callbacks | services | repositories | db/config |
|----------------|-------|------------|-----------|----------|-------------|-----------|
| **pages** | — | YES | YES | YES | NO | NO |
| **components** | NO | — | NO | NO | NO | NO |
| **callbacks** | NO | YES | — | YES | NO | NO |
| **services** | NO | NO | NO | — | YES | YES |
| **repositories** | NO | NO | NO | NO | — | YES |
| **db/config** | NO | NO | NO | NO | NO | — |

**Rule**: Only call downward. Never skip layers (pages must NOT call repositories directly).

## Current State (Pre-Refactor)

PM Hub currently uses a **flat structure**:
- `pages/` → imports directly from `utils/data_access.py` (repository-equivalent)
- `utils/data_access.py` → acts as both service and repository layer
- No `services/`, `repositories/`, `components/`, `callbacks/` directories yet

### Acceptable During Phase 1
- Pages importing from `utils/data_access.py` directly (flat architecture)
- No service layer yet (business logic minimal)

### Must Fix When Layered Architecture is Implemented
- Pages must go through services, not directly to repositories
- SQL must move from `utils/data_access.py` to `repositories/`
- Business logic must move from pages to `services/`

## SQL Placement Rules

| Location | SQL Allowed? |
|----------|-------------|
| `pages/` | NEVER |
| `components/` | NEVER |
| `callbacks/` | NEVER |
| `services/` | NEVER |
| `utils/data_access.py` | YES (current) |
| `repositories/` | YES (future) |
| `db/` | YES (migrations, schema) |
| `models/` | YES (DDL definitions) |

## Cross-Domain Rules

Within the same layer, avoid tight coupling:
- `portfolio_repo` should NOT import from `sprint_repo`
- `sprint_service` should NOT import from `portfolio_service` (use dependency injection or a shared service)
- Each domain should be independently testable
