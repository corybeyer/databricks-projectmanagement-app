"""Gate Repository — gate queries and decision operations."""

import pandas as pd
from repositories.base import query, write, safe_update
from models import sample_data


def get_gates(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get all non-deleted gates for a project's phases, ordered by gate_order."""
    return query("""
        SELECT g.*,
               ph.name as phase_name,
               ph.phase_order
        FROM gates g
        JOIN phases ph ON g.phase_id = ph.phase_id AND ph.is_deleted = false
        WHERE ph.project_id = :project_id
          AND g.is_deleted = false
        ORDER BY g.gate_order
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_gate_status)


def get_gate_by_id(gate_id: str, user_token: str = None) -> pd.DataFrame:
    """Get a single gate by ID."""
    return query("""
        SELECT g.*,
               ph.name as phase_name,
               ph.phase_order
        FROM gates g
        JOIN phases ph ON g.phase_id = ph.phase_id
        WHERE g.gate_id = :gate_id
          AND g.is_deleted = false
    """, params={"gate_id": gate_id}, user_token=user_token,
        sample_fallback=sample_data.get_gate_status)


def create_gate(gate_data: dict, user_token: str = None) -> bool:
    """Insert a new gate record."""
    allowed_columns = {
        "gate_id", "phase_id", "gate_order", "name", "status",
        "criteria", "decision", "decided_by", "decided_at",
        "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in gate_data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = gate_data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO gates ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="gates", record=gate_data,
    )


def update_gate_decision(gate_id: str, status: str, decision: str,
                         decided_by: str, user_email: str = None,
                         user_token: str = None) -> bool:
    """Update a gate's decision (approve/reject/defer)."""
    updates = {
        "status": status,
        "decision": decision,
        "decided_by": decided_by,
    }
    return safe_update(
        "gates", "gate_id", gate_id, updates,
        expected_updated_at=None,
        user_email=user_email, user_token=user_token,
    )
