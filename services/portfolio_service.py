"""Portfolio Service — KPI calculations, portfolio CRUD orchestration."""

import uuid
from repositories import portfolio_repo
from utils.validators import validate_portfolio_create, ValidationError


def get_dashboard_data(department_id: str = None, user_token: str = None) -> dict:
    """Get all data needed for the dashboard page.

    Enforces RBAC department filtering: non-admin users only see
    portfolios from their own department.
    """
    from services.auth_service import get_current_user, get_department_filter
    user = get_current_user()
    dept = get_department_filter(user)
    effective_dept = dept if dept is not None else department_id

    portfolios = portfolio_repo.get_portfolios(
        department_id=effective_dept, user_token=user_token,
    )

    if portfolios.empty:
        return {
            "portfolios": portfolios,
            "total_projects": 0, "avg_completion": 0,
            "total_budget": 0, "total_spent": 0,
            "green_count": 0, "yellow_count": 0, "red_count": 0,
        }

    return {
        "portfolios": portfolios,
        "total_projects": int(portfolios["project_count"].sum()),
        "avg_completion": float(portfolios["avg_completion"].mean()),
        "total_budget": float(portfolios["total_budget"].sum()),
        "total_spent": float(portfolios["total_spent"].sum()),
        "green_count": len(portfolios[portfolios["health"] == "green"]),
        "yellow_count": len(portfolios[portfolios["health"] == "yellow"]),
        "red_count": len(portfolios[portfolios["health"] == "red"]),
    }


def get_portfolio_projects(portfolio_id: str, user_token: str = None):
    return portfolio_repo.get_portfolio_projects(portfolio_id, user_token=user_token)


def get_portfolio(portfolio_id: str, user_token: str = None):
    """Get a single portfolio by ID."""
    return portfolio_repo.get_portfolio_by_id(portfolio_id, user_token=user_token)


def create_portfolio_from_form(form_data: dict, user_email: str = None,
                               user_token: str = None) -> dict:
    """Validate and create a portfolio. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "create", "portfolio"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_portfolio_create(
            name=form_data.get("name"),
            owner=form_data.get("owner"),
            description=form_data.get("description"),
            strategic_priority=form_data.get("strategic_priority"),
            department_id=form_data.get("department_id"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    portfolio_data = {
        "portfolio_id": f"pf-{str(uuid.uuid4())[:6]}",
        "name": cleaned["name"],
        "owner": cleaned["owner"],
        "status": "active",
        "health": "green",
        "created_by": user_email,
    }

    # Optional fields
    if cleaned.get("description"):
        portfolio_data["description"] = cleaned["description"]
    if cleaned.get("strategic_priority"):
        portfolio_data["strategic_priority"] = cleaned["strategic_priority"]
    if cleaned.get("department_id"):
        portfolio_data["department_id"] = cleaned["department_id"]

    success = portfolio_repo.create_portfolio(portfolio_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {},
                "message": f"Portfolio '{cleaned['name']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create portfolio"}


def update_portfolio_from_form(portfolio_id: str, form_data: dict,
                               expected_updated_at: str,
                               user_email: str = None,
                               user_token: str = None) -> dict:
    """Validate and update a portfolio. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "portfolio"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_portfolio_create(
            name=form_data.get("name"),
            owner=form_data.get("owner"),
            description=form_data.get("description"),
            strategic_priority=form_data.get("strategic_priority"),
            department_id=form_data.get("department_id"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "name": cleaned["name"],
        "owner": cleaned["owner"],
    }
    for field in ("description", "strategic_priority", "department_id"):
        if cleaned.get(field) is not None:
            updates[field] = cleaned[field]

    success = portfolio_repo.update_portfolio(
        portfolio_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {},
                "message": f"Portfolio '{cleaned['name']}' updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_portfolio(portfolio_id: str, user_email: str = None,
                     user_token: str = None) -> bool:
    """Soft-delete a portfolio."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "delete", "portfolio"):
        return False
    return portfolio_repo.delete_portfolio(
        portfolio_id, user_email=user_email, user_token=user_token,
    )
