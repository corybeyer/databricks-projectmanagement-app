"""Resource Repository — team members, project assignments, and allocations."""

import pandas as pd
from repositories.base import query, write, safe_update, soft_delete
from models import sample_data


def get_resource_allocations(user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT tm.user_id, tm.display_name, tm.role,
               pr.name as project_name,
               pr.project_id,
               COUNT(DISTINCT t.task_id) as task_count,
               SUM(t.story_points) as points_assigned,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as points_done
        FROM team_members tm
        LEFT JOIN tasks t ON tm.user_id = t.assignee AND t.status != 'done' AND t.is_deleted = false
        LEFT JOIN projects pr ON t.project_id = pr.project_id
        WHERE tm.is_active = true
        GROUP BY ALL
        ORDER BY tm.display_name, pr.name
    """, user_token=user_token, sample_fallback=sample_data.get_resource_allocations)


def get_retro_items(sprint_id: str, user_token: str = None) -> pd.DataFrame:
    return query("""
        SELECT ri.*
        FROM retro_items ri
        WHERE ri.sprint_id = :sprint_id
          AND ri.is_deleted = false
        ORDER BY ri.votes DESC
    """, params={"sprint_id": sprint_id}, user_token=user_token,
        sample_fallback=sample_data.get_retro_items)


# ── Team Members ──────────────────────────────────────────────────


def get_team_members(department_id: str = None, user_token: str = None) -> pd.DataFrame:
    """Get all active team members, optionally filtered by department."""
    if department_id:
        return query("""
            SELECT tm.*
            FROM team_members tm
            WHERE tm.is_active = true
              AND tm.is_deleted = false
              AND tm.department_id = :department_id
            ORDER BY tm.display_name
        """, params={"department_id": department_id}, user_token=user_token,
            sample_fallback=sample_data.get_team_members)

    return query("""
        SELECT tm.*
        FROM team_members tm
        WHERE tm.is_active = true
          AND tm.is_deleted = false
        ORDER BY tm.display_name
    """, user_token=user_token, sample_fallback=sample_data.get_team_members)


def get_project_team(project_id: str, user_token: str = None) -> pd.DataFrame:
    """Get project_team records with member details (JOIN team_members)."""
    return query("""
        SELECT pt.project_id, pt.user_id, pt.project_role,
               pt.allocation_pct, pt.start_date, pt.end_date,
               pt.created_at, pt.updated_at,
               tm.display_name, tm.email, tm.role as team_role,
               tm.department_id
        FROM project_team pt
        JOIN team_members tm ON pt.user_id = tm.user_id
        WHERE pt.project_id = :project_id
          AND pt.is_deleted = false
          AND tm.is_deleted = false
        ORDER BY tm.display_name
    """, params={"project_id": project_id}, user_token=user_token,
        sample_fallback=sample_data.get_project_team)


def create_assignment(data: dict, user_token: str = None) -> bool:
    """Insert a new project_team record."""
    allowed_columns = {
        "project_id", "user_id", "project_role", "allocation_pct",
        "start_date", "end_date", "created_by",
    }
    params = {}
    used_cols = []
    for col in allowed_columns:
        if col in data:
            if not col.isidentifier():
                raise ValueError(f"Invalid column name: {col!r}")
            used_cols.append(col)
            params[col] = data[col]

    col_list = ", ".join(used_cols)
    param_list = ", ".join(f":{col}" for col in used_cols)
    return write(
        f"INSERT INTO project_team ({col_list}) VALUES ({param_list})",
        params=params, user_token=user_token,
        table_name="project_team", record=data,
    )


def update_assignment(project_id: str, user_id: str, updates: dict,
                      expected_updated_at: str, user_email: str = None,
                      user_token: str = None) -> bool:
    """Update a project_team record using optimistic locking.

    project_team has a composite PK (project_id, user_id) so we use
    safe_update on user_id and then filter by project_id in the updates.
    For the in-memory store we do a manual update instead.
    """
    from repositories.base import _use_sample_data, _validate_identifier, ALLOWED_TABLES
    if _use_sample_data():
        from models import sample_data as sd
        if "project_team" not in sd._store:
            sd._get_store("project_team", sd._init_project_team)
        df = sd._store["project_team"]
        mask = (df["project_id"] == project_id) & (df["user_id"] == user_id)
        if "is_deleted" in df.columns:
            mask = mask & (df["is_deleted"] == False)  # noqa: E712
        if mask.sum() == 0:
            return False
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if user_email:
            updates["updated_by"] = user_email
        updates["updated_at"] = now
        for col, val in updates.items():
            if col in df.columns:
                df.loc[mask, col] = val
        return True

    # UC path: build a composite WHERE clause
    from repositories.base import ALLOWED_UPDATE_COLUMNS
    _validate_identifier("project_team", ALLOWED_TABLES, "table")
    for col in updates:
        if col not in ALLOWED_UPDATE_COLUMNS.get("project_team", set()):
            raise ValueError(f"Column {col!r} not allowed for update on table 'project_team'")

    if user_email:
        updates = {**updates, "updated_by": user_email}

    set_clauses = ", ".join(f"{col} = :{col}" for col in updates)
    if expected_updated_at is not None:
        sql_str = (
            f"UPDATE project_team SET {set_clauses}, updated_at = current_timestamp() "
            f"WHERE project_id = :_project_id AND user_id = :_user_id "
            f"AND updated_at = :_expected_updated_at"
        )
        params = {**updates, "_project_id": project_id, "_user_id": user_id,
                  "_expected_updated_at": expected_updated_at}
    else:
        sql_str = (
            f"UPDATE project_team SET {set_clauses}, updated_at = current_timestamp() "
            f"WHERE project_id = :_project_id AND user_id = :_user_id "
            f"AND is_deleted = false"
        )
        params = {**updates, "_project_id": project_id, "_user_id": user_id}
    return write(sql_str, params=params, user_token=user_token)


def delete_assignment(project_id: str, user_id: str,
                      user_email: str = None, user_token: str = None) -> bool:
    """Soft-delete a project_team record (composite PK)."""
    from repositories.base import _use_sample_data, _validate_identifier, ALLOWED_TABLES
    if _use_sample_data():
        from models import sample_data as sd
        if "project_team" not in sd._store:
            sd._get_store("project_team", sd._init_project_team)
        df = sd._store["project_team"]
        mask = (df["project_id"] == project_id) & (df["user_id"] == user_id)
        if "is_deleted" in df.columns:
            mask = mask & (df["is_deleted"] == False)  # noqa: E712
        if mask.sum() == 0:
            return False
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.loc[mask, "is_deleted"] = True
        if "deleted_at" in df.columns:
            df.loc[mask, "deleted_at"] = now
        if "deleted_by" in df.columns and user_email:
            df.loc[mask, "deleted_by"] = user_email
        df.loc[mask, "updated_at"] = now
        return True

    _validate_identifier("project_team", ALLOWED_TABLES, "table")
    deleted_by_clause = ", deleted_by = :_email" if user_email else ""
    sql_str = (
        f"UPDATE project_team SET is_deleted = true, deleted_at = current_timestamp(), "
        f"updated_at = current_timestamp(){deleted_by_clause} "
        f"WHERE project_id = :_project_id AND user_id = :_user_id AND is_deleted = false"
    )
    params = {"_project_id": project_id, "_user_id": user_id}
    if user_email:
        params["_email"] = user_email
    return write(sql_str, params=params, user_token=user_token)


def get_allocation_summary(department_id: str = None, user_token: str = None) -> pd.DataFrame:
    """SUM allocation_pct per user across all active project assignments."""
    if department_id:
        return query("""
            SELECT tm.user_id, tm.display_name, tm.email, tm.role,
                   tm.department_id, tm.capacity_pct,
                   COALESCE(SUM(pt.allocation_pct), 0) as total_allocation,
                   COUNT(pt.project_id) as project_count
            FROM team_members tm
            LEFT JOIN project_team pt ON tm.user_id = pt.user_id AND pt.is_deleted = false
            WHERE tm.is_active = true
              AND tm.is_deleted = false
              AND tm.department_id = :department_id
            GROUP BY tm.user_id, tm.display_name, tm.email, tm.role,
                     tm.department_id, tm.capacity_pct
            ORDER BY total_allocation DESC
        """, params={"department_id": department_id}, user_token=user_token,
            sample_fallback=sample_data.get_project_team)

    return query("""
        SELECT tm.user_id, tm.display_name, tm.email, tm.role,
               tm.department_id, tm.capacity_pct,
               COALESCE(SUM(pt.allocation_pct), 0) as total_allocation,
               COUNT(pt.project_id) as project_count
        FROM team_members tm
        LEFT JOIN project_team pt ON tm.user_id = pt.user_id AND pt.is_deleted = false
        WHERE tm.is_active = true
          AND tm.is_deleted = false
        GROUP BY tm.user_id, tm.display_name, tm.email, tm.role,
                 tm.department_id, tm.capacity_pct
        ORDER BY total_allocation DESC
    """, user_token=user_token, sample_fallback=sample_data.get_project_team)
