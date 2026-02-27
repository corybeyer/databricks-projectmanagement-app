"""Phase Service — phase & gate lifecycle management with validation."""

import uuid
from datetime import datetime
from repositories import phase_repo, gate_repo
from utils.validators import (
    validate_phase_create, validate_gate_create, validate_enum,
    ValidationError, GATE_STATUSES,
)


# ── Phase CRUD ──────────────────────────────────────────────────────


def get_phases(project_id: str, user_token: str = None):
    """Get all phases for a project."""
    return phase_repo.get_phases(project_id, user_token=user_token)


def get_phase(phase_id: str, user_token: str = None):
    """Get a single phase by ID."""
    return phase_repo.get_phase_by_id(phase_id, user_token=user_token)


def create_phase_from_form(form_data: dict, user_email: str = None,
                           user_token: str = None) -> dict:
    """Validate and create a phase. Returns result dict."""
    try:
        cleaned = validate_phase_create(
            name=form_data.get("name"),
            phase_type=form_data.get("phase_type"),
            delivery_method=form_data.get("delivery_method"),
            phase_order=form_data.get("phase_order"),
            start_date=form_data.get("start_date"),
            end_date=form_data.get("end_date"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    phase_data = {
        "phase_id": f"ph-{str(uuid.uuid4())[:6]}",
        "project_id": form_data.get("project_id", "prj-001"),
        "name": cleaned["name"],
        "phase_type": cleaned["phase_type"],
        "delivery_method": cleaned["delivery_method"],
        "phase_order": cleaned["phase_order"],
        "status": "not_started",
        "pct_complete": 0,
        "created_by": user_email,
    }

    # Optional date fields
    if cleaned.get("start_date"):
        phase_data["start_date"] = str(cleaned["start_date"])
    if cleaned.get("end_date"):
        phase_data["end_date"] = str(cleaned["end_date"])

    success = phase_repo.create_phase(phase_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {},
                "message": f"Phase '{cleaned['name']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create phase"}


def update_phase_from_form(phase_id: str, form_data: dict,
                           expected_updated_at: str,
                           user_email: str = None,
                           user_token: str = None) -> dict:
    """Validate and update a phase. Returns result dict."""
    try:
        cleaned = validate_phase_create(
            name=form_data.get("name"),
            phase_type=form_data.get("phase_type"),
            delivery_method=form_data.get("delivery_method"),
            phase_order=form_data.get("phase_order"),
            start_date=form_data.get("start_date"),
            end_date=form_data.get("end_date"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    updates = {
        "name": cleaned["name"],
        "phase_type": cleaned["phase_type"],
        "delivery_method": cleaned["delivery_method"],
        "phase_order": cleaned["phase_order"],
    }

    if cleaned.get("start_date"):
        updates["start_date"] = str(cleaned["start_date"])
    if cleaned.get("end_date"):
        updates["end_date"] = str(cleaned["end_date"])

    # Allow status update if provided
    status = form_data.get("status")
    if status:
        updates["status"] = status

    success = phase_repo.update_phase(
        phase_id, updates, expected_updated_at,
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "errors": {},
                "message": f"Phase '{cleaned['name']}' updated"}
    return {"success": False, "errors": {},
            "message": "Update conflict — record was modified by another user"}


def delete_phase(phase_id: str, user_email: str = None,
                 user_token: str = None) -> bool:
    """Soft-delete a phase."""
    return phase_repo.delete_phase(
        phase_id, user_email=user_email, user_token=user_token,
    )


# ── Gate Operations ─────────────────────────────────────────────────


def get_gates(project_id: str, user_token: str = None):
    """Get all gates for a project."""
    return gate_repo.get_gates(project_id, user_token=user_token)


def get_gate(gate_id: str, user_token: str = None):
    """Get a single gate by ID."""
    return gate_repo.get_gate_by_id(gate_id, user_token=user_token)


def create_gate_from_form(form_data: dict, user_email: str = None,
                          user_token: str = None) -> dict:
    """Validate and create a gate. Returns result dict."""
    try:
        cleaned = validate_gate_create(
            name=form_data.get("name"),
            criteria=form_data.get("criteria"),
        )
    except ValidationError as exc:
        return {"success": False, "errors": {exc.field: exc.message}, "message": exc.message}

    gate_data = {
        "gate_id": f"g-{str(uuid.uuid4())[:6]}",
        "phase_id": form_data.get("phase_id"),
        "gate_order": form_data.get("gate_order", 1),
        "name": cleaned["name"],
        "status": "pending",
        "created_by": user_email,
    }
    if cleaned.get("criteria"):
        gate_data["criteria"] = cleaned["criteria"]

    success = gate_repo.create_gate(gate_data, user_token=user_token)
    if success:
        return {"success": True, "errors": {},
                "message": f"Gate '{cleaned['name']}' created"}
    return {"success": False, "errors": {}, "message": "Failed to create gate"}


def approve_gate(gate_id: str, decision: str, user_email: str = None,
                 user_token: str = None) -> dict:
    """Approve a gate with decision notes."""
    success = gate_repo.update_gate_decision(
        gate_id, status="approved", decision=decision or "Approved",
        decided_by=user_email or "Unknown",
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Gate approved"}
    return {"success": False, "message": "Failed to approve gate"}


def reject_gate(gate_id: str, decision: str, user_email: str = None,
                user_token: str = None) -> dict:
    """Reject a gate with decision notes."""
    success = gate_repo.update_gate_decision(
        gate_id, status="rejected", decision=decision or "Rejected",
        decided_by=user_email or "Unknown",
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Gate rejected"}
    return {"success": False, "message": "Failed to reject gate"}


def defer_gate(gate_id: str, decision: str, user_email: str = None,
               user_token: str = None) -> dict:
    """Defer a gate with decision notes."""
    success = gate_repo.update_gate_decision(
        gate_id, status="deferred", decision=decision or "Deferred",
        decided_by=user_email or "Unknown",
        user_email=user_email, user_token=user_token,
    )
    if success:
        return {"success": True, "message": "Gate deferred"}
    return {"success": False, "message": "Failed to defer gate"}
