"""
PostgreSQL Connection — Placeholder
====================================
Future OLTP store for PM Hub. Not yet implemented.
PostgreSQL will handle CRUD operations; Unity Catalog
will handle analytics with Delta time travel.
"""


def get_engine():
    raise NotImplementedError(
        "PostgreSQL not yet configured. "
        "See docs/architecture-plan.md for the data split strategy."
    )
