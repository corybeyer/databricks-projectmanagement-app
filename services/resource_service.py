"""Resource Service — team member and project assignment management."""

from repositories import resource_repo
from utils.validators import validate_assignment_create, ValidationError


def get_team_members(department_id: str = None, user_token: str = None):
    """Get team members, optionally filtered by department."""
    return resource_repo.get_team_members(
        department_id=department_id, user_token=user_token,
    )


def get_project_assignments(project_id: str, user_token: str = None):
    """Get project_team records with member details for a project."""
    return resource_repo.get_project_team(
        project_id=project_id, user_token=user_token,
    )


def assign_member_to_project(form_data: dict, user_email: str = None,
                              user_token: str = None) -> dict:
    """Validate and create a project_team record. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "create", "resource"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_assignment_create(
            project_id=form_data.get("project_id"),
            user_id=form_data.get("user_id"),
            project_role=form_data.get("project_role"),
            allocation_pct=form_data.get("allocation_pct"),
            start_date=form_data.get("start_date"),
            end_date=form_data.get("end_date"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    assignment_data = {
        "project_id": cleaned["project_id"],
        "user_id": cleaned["user_id"],
        "project_role": cleaned["project_role"],
        "allocation_pct": cleaned["allocation_pct"],
        "created_by": user_email,
    }

    if cleaned.get("start_date"):
        assignment_data["start_date"] = str(cleaned["start_date"])
    if cleaned.get("end_date"):
        assignment_data["end_date"] = str(cleaned["end_date"])

    success = resource_repo.create_assignment(assignment_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {}, "message": "Team member assigned to project"}
    return {"success": False, "errors": {}, "message": "Failed to create assignment"}


def update_assignment(project_id: str, user_id: str, form_data: dict,
                      expected_updated_at: str, user_email: str = None,
                      user_token: str = None) -> dict:
    """Validate and update a project_team record. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "resource"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    updates = {}

    # Validate optional fields that may be updated
    if "project_role" in form_data and form_data["project_role"]:
        from utils.validators import validate_enum, PROJECT_ROLES
        try:
            updates["project_role"] = validate_enum(
                form_data["project_role"], PROJECT_ROLES, "project_role",
            )
        except ValidationError as exc:
            return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    if "allocation_pct" in form_data and form_data["allocation_pct"] is not None:
        from utils.validators import validate_integer
        try:
            updates["allocation_pct"] = validate_integer(
                form_data["allocation_pct"], "allocation_pct", min_val=0, max_val=100,
            )
        except ValidationError as exc:
            return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    if "start_date" in form_data and form_data["start_date"]:
        from utils.validators import validate_date
        try:
            val = validate_date(form_data["start_date"], "start_date", required=False)
            if val:
                updates["start_date"] = str(val)
        except ValidationError as exc:
            return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    if "end_date" in form_data and form_data["end_date"]:
        from utils.validators import validate_date
        try:
            val = validate_date(form_data["end_date"], "end_date", required=False)
            if val:
                updates["end_date"] = str(val)
        except ValidationError as exc:
            return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    if not updates:
        return {"success": False, "errors": {}, "message": "No fields to update"}

    success = resource_repo.update_assignment(
        project_id, user_id, updates,
        expected_updated_at=expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {}, "message": "Assignment updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def remove_assignment(project_id: str, user_id: str,
                      user_email: str = None, user_token: str = None) -> dict:
    """Soft-delete a project_team record. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "delete", "resource"):
        return {"success": False, "message": "Permission denied"}
    success = resource_repo.delete_assignment(
        project_id, user_id, user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Assignment removed"}
    return {"success": False, "message": "Failed to remove assignment"}


def get_capacity_overview(department_id: str = None, user_token: str = None):
    """Get total allocation % per user across all projects.

    Returns a DataFrame with user_id, display_name, total_allocation, project_count.
    Uses allocation_summary from repo when available; falls back to computing
    from project_team records in sample data mode.
    """
    summary = resource_repo.get_allocation_summary(
        department_id=department_id, user_token=user_token,
    )

    # If sample_fallback returned raw project_team, compute the aggregation
    if not summary.empty and "total_allocation" not in summary.columns:
        import pandas as pd
        members = resource_repo.get_team_members(
            department_id=department_id, user_token=user_token,
        )
        if summary.empty or "allocation_pct" not in summary.columns:
            return pd.DataFrame(columns=[
                "user_id", "display_name", "email", "role",
                "department_id", "capacity_pct", "total_allocation", "project_count",
            ])
        agg = (
            summary.groupby("user_id")
            .agg(total_allocation=("allocation_pct", "sum"),
                 project_count=("project_id", "count"))
            .reset_index()
        )
        if not members.empty:
            result = members.merge(agg, on="user_id", how="left")
            result["total_allocation"] = result["total_allocation"].fillna(0).astype(int)
            result["project_count"] = result["project_count"].fillna(0).astype(int)
            return result
        return agg

    return summary


def get_over_allocated_members(department_id: str = None, user_token: str = None):
    """Get team members whose total allocation exceeds 100%."""
    capacity = get_capacity_overview(
        department_id=department_id, user_token=user_token,
    )
    if capacity.empty or "total_allocation" not in capacity.columns:
        import pandas as pd
        return pd.DataFrame()
    return capacity[capacity["total_allocation"] > 100]
