"""Risk Service — PMI risk lifecycle management with validation."""

import uuid
from datetime import date
from repositories import risk_repo
from utils.validators import validate_risk_create, validate_enum, ValidationError, RISK_STATUSES


def get_risks(portfolio_id: str = None, user_token: str = None):
    return risk_repo.get_risks(portfolio_id=portfolio_id, user_token=user_token)


def get_risk(risk_id: str, user_token: str = None):
    return risk_repo.get_risk_detail(risk_id, user_token=user_token)


def get_risks_by_project(project_id: str, user_token: str = None):
    return risk_repo.get_risks_by_project(project_id, user_token=user_token)


def create_risk_from_form(form_data: dict, user_email: str = None,
                          user_token: str = None) -> dict:
    """Validate and create a risk. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "create", "risk"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_risk_create(
            title=form_data.get("title"),
            category=form_data.get("category"),
            probability=form_data.get("probability"),
            impact=form_data.get("impact"),
            response_strategy=form_data.get("response_strategy"),
            risk_proximity=form_data.get("risk_proximity"),
            description=form_data.get("description"),
            mitigation_plan=form_data.get("mitigation_plan"),
            contingency_plan=form_data.get("contingency_plan"),
            trigger_conditions=form_data.get("trigger_conditions"),
            owner=form_data.get("owner"),
            response_owner=form_data.get("response_owner"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    risk_data = {
        "risk_id": str(uuid.uuid4())[:8],
        "title": cleaned["title"],
        "category": cleaned["category"],
        "probability": cleaned["probability"],
        "impact": cleaned["impact"],
        "risk_score": cleaned.get("risk_score", cleaned["probability"] * cleaned["impact"]),
        "status": "identified",
        "identified_date": str(date.today()),
        "last_review_date": str(date.today()),
        "project_id": form_data.get("project_id", "prj-001"),
        "portfolio_id": form_data.get("portfolio_id", "pf-001"),
        "created_by": user_email,
    }

    # Optional fields
    if cleaned.get("response_strategy"):
        risk_data["response_strategy"] = cleaned["response_strategy"]
    if cleaned.get("risk_proximity"):
        risk_data["risk_proximity"] = cleaned["risk_proximity"]
    if cleaned.get("description"):
        risk_data["description"] = cleaned["description"]
    if cleaned.get("mitigation_plan"):
        risk_data["mitigation_plan"] = cleaned["mitigation_plan"]
    if cleaned.get("contingency_plan"):
        risk_data["contingency_plan"] = cleaned["contingency_plan"]
    if cleaned.get("trigger_conditions"):
        risk_data["trigger_conditions"] = cleaned["trigger_conditions"]
    if cleaned.get("owner"):
        risk_data["owner"] = cleaned["owner"]
    if cleaned.get("response_owner"):
        risk_data["response_owner"] = cleaned["response_owner"]

    risk_urgency = form_data.get("risk_urgency")
    if risk_urgency is not None:
        try:
            risk_data["risk_urgency"] = int(risk_urgency)
        except (ValueError, TypeError):
            pass

    success = risk_repo.create_risk(risk_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {}, "message": f"Risk '{cleaned['title']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create risk"}


def update_risk_from_form(risk_id: str, form_data: dict, expected_updated_at: str,
                          user_email: str = None, user_token: str = None) -> dict:
    """Validate and update a risk. Returns result dict."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "risk"):
        return {"success": False, "message": "Permission denied", "errors": {}}
    try:
        cleaned = validate_risk_create(
            title=form_data.get("title"),
            category=form_data.get("category"),
            probability=form_data.get("probability"),
            impact=form_data.get("impact"),
            response_strategy=form_data.get("response_strategy"),
            risk_proximity=form_data.get("risk_proximity"),
            description=form_data.get("description"),
            mitigation_plan=form_data.get("mitigation_plan"),
            contingency_plan=form_data.get("contingency_plan"),
            trigger_conditions=form_data.get("trigger_conditions"),
            owner=form_data.get("owner"),
            response_owner=form_data.get("response_owner"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "title": cleaned["title"],
        "category": cleaned["category"],
        "probability": cleaned["probability"],
        "impact": cleaned["impact"],
        "risk_score": cleaned.get("risk_score", cleaned["probability"] * cleaned["impact"]),
    }

    # Optional fields — always update if present in cleaned data
    for key in ("response_strategy", "risk_proximity", "description",
                "mitigation_plan", "contingency_plan", "trigger_conditions",
                "owner", "response_owner"):
        if cleaned.get(key) is not None:
            updates[key] = cleaned[key]

    risk_urgency = form_data.get("risk_urgency")
    if risk_urgency is not None:
        try:
            updates["risk_urgency"] = int(risk_urgency)
        except (ValueError, TypeError):
            pass

    success = risk_repo.update_risk(
        risk_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {}, "message": f"Risk '{cleaned['title']}' updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_risk(risk_id: str, user_email: str = None, user_token: str = None) -> bool:
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "delete", "risk"):
        return False
    return risk_repo.delete_risk(risk_id, user_email=user_email, user_token=user_token)


def update_risk_status(risk_id: str, new_status: str, user_email: str = None,
                       user_token: str = None) -> dict:
    """Update risk status following PMI lifecycle transitions."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "risk"):
        return {"success": False, "message": "Permission denied"}
    try:
        validated_status = validate_enum(new_status, RISK_STATUSES, "status")
    except ValidationError as exc:
        return {"success": False, "message": exc.message}

    success = risk_repo.update_risk_status(
        risk_id, validated_status, user_email=user_email, user_token=user_token,
    )
    if success:
        label = new_status.replace("_", " ").title()
        return {"success": True, "message": f"Risk status changed to {label}"}
    return {"success": False, "message": "Failed to update risk status"}


def review_risk(risk_id: str, user_email: str = None, user_token: str = None) -> dict:
    """Mark a risk as reviewed today."""
    from services.auth_service import get_current_user, has_permission
    user = get_current_user()
    if not has_permission(user, "update", "risk"):
        return {"success": False, "message": "Permission denied"}
    risk_df = risk_repo.get_risk_detail(risk_id, user_token=user_token)
    if risk_df.empty:
        return {"success": False, "message": "Risk not found"}
    expected = str(risk_df.iloc[0].get("updated_at", ""))
    success = risk_repo.update_risk(
        risk_id,
        {"last_review_date": str(date.today())},
        expected_updated_at=expected or None,
        user_email=user_email,
        user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Risk reviewed"}
    return {"success": False, "message": "Failed to mark risk as reviewed"}
