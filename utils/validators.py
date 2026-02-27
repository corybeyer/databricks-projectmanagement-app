"""Input Validation — shared validation functions for service layer.

Called by services before passing data to repositories.
Never import Dash here. All functions accept/return pure Python types.
"""

import re
import uuid
from datetime import date, datetime
from typing import Optional, List


# ── Exceptions & Result Container ────────────────────────────────────

class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ValidationResult:
    """Collects multiple validation errors for batch reporting."""

    def __init__(self):
        self.errors: List[ValidationError] = []

    def add_error(self, field: str, message: str):
        self.errors.append(ValidationError(field, message))

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def raise_if_invalid(self):
        """Raise the first error with all messages joined."""
        if not self.is_valid:
            raise ValidationError(
                self.errors[0].field,
                "; ".join(f"{e.field}: {e.message}" for e in self.errors),
            )


# ── Domain Enums (from models/schema_ddl.sql) ───────────────────────

# tasks.status — backlog | todo | in_progress | review | done
TASK_STATUSES = {"backlog", "todo", "in_progress", "review", "done", "blocked"}

# projects.status
PROJECT_STATUSES = {"planning", "active", "on_hold", "completed", "cancelled"}

# sprints.status — DDL says planning | active | review | closed
SPRINT_STATUSES = {"planning", "active", "review", "closed"}

# risks.status
RISK_STATUSES = {
    "identified",
    "qualitative_analysis",
    "response_planning",
    "monitoring",
    "resolved",
    "closed",
}

# project_charters implicit statuses
CHARTER_STATUSES = {"draft", "submitted", "under_review", "approved", "rejected"}

# gates.status
GATE_STATUSES = {"pending", "approved", "rejected", "deferred"}

# projects.delivery_method / phases.delivery_method
DELIVERY_METHODS = {"waterfall", "agile", "hybrid"}

# tasks.task_type — DDL says epic | story | task | bug | subtask
TASK_TYPES = {"epic", "story", "task", "bug", "subtask"}

# tasks.priority
PRIORITY_LEVELS = {"critical", "high", "medium", "low"}

# risks.category
RISK_CATEGORIES = {
    "technical",
    "resource",
    "schedule",
    "scope",
    "budget",
    "external",
    "organizational",
}

# risks.response_strategy
RISK_RESPONSE_STRATEGIES = {"avoid", "transfer", "mitigate", "accept", "escalate"}

# risks.risk_proximity
RISK_PROXIMITY = {"near_term", "mid_term", "long_term"}

# retro_items.category — DDL says went_well | improve | action_item
RETRO_CATEGORIES = {"went_well", "improve", "action_item"}

# dependencies.dependency_type
DEPENDENCY_TYPES = {"blocking", "dependent", "shared_resource", "informational"}

# portfolios.status
PORTFOLIO_STATUSES = {"active", "on_hold", "archived"}

# portfolios.health / projects.health
HEALTH_VALUES = {"green", "yellow", "red"}

# phases.phase_type
PHASE_TYPES = {
    "initiation",
    "planning",
    "design",
    "build",
    "test",
    "deploy",
    "closeout",
}

# phases.status
PHASE_STATUSES = {"not_started", "active", "complete"}

# deliverables.status
DELIVERABLE_STATUSES = {"not_started", "in_progress", "complete", "approved"}

# dependencies.risk_level
DEPENDENCY_RISK_LEVELS = {"high", "medium", "low"}

# dependencies.status
DEPENDENCY_STATUSES = {"active", "resolved", "accepted"}

# team_members.role
TEAM_ROLES = {"admin", "lead", "engineer", "analyst", "viewer"}

# project_team.project_role
PROJECT_ROLES = {"pm", "lead", "engineer", "analyst", "stakeholder"}

# audit_log.action
AUDIT_ACTIONS = {"create", "update", "delete", "approve", "reject"}

# Regex for project-style short IDs (e.g. prj-001, sp-004, ret-001)
_SHORT_ID_RE = re.compile(r"^[a-z]{1,10}-\d{1,6}$")

# Regex for email (RFC 5322 simplified)
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)


# ── Individual Validators ────────────────────────────────────────────

def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate and return a UUID string.

    Accepts standard UUID format (with or without hyphens) and
    project-style short IDs like ``prj-001``, ``sp-004``.
    """
    if value is None:
        raise ValidationError(field_name, "is required")
    if not isinstance(value, str):
        raise ValidationError(field_name, "must be a string")

    stripped = value.strip()
    if not stripped:
        raise ValidationError(field_name, "must not be empty")

    # Accept project-style short IDs
    if _SHORT_ID_RE.match(stripped):
        return stripped

    # Accept standard UUIDs (with or without hyphens)
    try:
        parsed = uuid.UUID(stripped)
        return str(parsed)
    except (ValueError, AttributeError):
        raise ValidationError(
            field_name,
            f"invalid identifier format: '{stripped}' "
            "(expected UUID or short ID like 'prj-001')",
        )


def validate_string(
    value: str,
    field_name: str,
    min_length: int = 1,
    max_length: int = 500,
    required: bool = True,
) -> Optional[str]:
    """Validate a string field with length constraints.

    Returns the stripped string or ``None`` if optional and empty.
    """
    if value is None:
        if required:
            raise ValidationError(field_name, "is required")
        return None

    if not isinstance(value, str):
        raise ValidationError(field_name, "must be a string")

    stripped = value.strip()

    if not stripped:
        if required:
            raise ValidationError(field_name, "must not be empty")
        return None

    if len(stripped) < min_length:
        raise ValidationError(
            field_name,
            f"must be at least {min_length} character(s), got {len(stripped)}",
        )

    if len(stripped) > max_length:
        raise ValidationError(
            field_name,
            f"must be at most {max_length} character(s), got {len(stripped)}",
        )

    return stripped


def validate_enum(
    value: str,
    allowed_values: set,
    field_name: str,
    required: bool = True,
) -> Optional[str]:
    """Validate that value is one of the allowed values.

    Comparison is case-insensitive; returns the lowercase canonical form.
    """
    if value is None:
        if required:
            raise ValidationError(field_name, "is required")
        return None

    if not isinstance(value, str):
        raise ValidationError(field_name, "must be a string")

    normalised = value.strip().lower()

    if not normalised:
        if required:
            raise ValidationError(field_name, "must not be empty")
        return None

    if normalised not in allowed_values:
        sorted_vals = sorted(allowed_values)
        raise ValidationError(
            field_name,
            f"must be one of {sorted_vals}, got '{normalised}'",
        )

    return normalised


def validate_integer(
    value,
    field_name: str,
    min_val: int = None,
    max_val: int = None,
    required: bool = True,
) -> Optional[int]:
    """Validate an integer value with optional range constraints."""
    if value is None:
        if required:
            raise ValidationError(field_name, "is required")
        return None

    try:
        int_val = int(value)
    except (ValueError, TypeError):
        raise ValidationError(field_name, f"must be an integer, got '{value}'")

    # Reject booleans masquerading as ints
    if isinstance(value, bool):
        raise ValidationError(field_name, f"must be an integer, got boolean")

    if min_val is not None and int_val < min_val:
        raise ValidationError(
            field_name, f"must be >= {min_val}, got {int_val}"
        )

    if max_val is not None and int_val > max_val:
        raise ValidationError(
            field_name, f"must be <= {max_val}, got {int_val}"
        )

    return int_val


def validate_float(
    value,
    field_name: str,
    min_val: float = None,
    max_val: float = None,
    required: bool = True,
) -> Optional[float]:
    """Validate a float/numeric value with optional range constraints."""
    if value is None:
        if required:
            raise ValidationError(field_name, "is required")
        return None

    try:
        float_val = float(value)
    except (ValueError, TypeError):
        raise ValidationError(field_name, f"must be a number, got '{value}'")

    if min_val is not None and float_val < min_val:
        raise ValidationError(
            field_name, f"must be >= {min_val}, got {float_val}"
        )

    if max_val is not None and float_val > max_val:
        raise ValidationError(
            field_name, f"must be <= {max_val}, got {float_val}"
        )

    return float_val


def validate_date(
    value,
    field_name: str,
    required: bool = True,
    min_date: date = None,
    max_date: date = None,
) -> Optional[date]:
    """Validate a date value.

    Accepts ``datetime.date``, ``datetime.datetime``, or ISO-format string
    (``YYYY-MM-DD``).
    """
    if value is None:
        if required:
            raise ValidationError(field_name, "is required")
        return None

    if isinstance(value, datetime):
        date_val = value.date()
    elif isinstance(value, date):
        date_val = value
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            if required:
                raise ValidationError(field_name, "is required")
            return None
        try:
            date_val = date.fromisoformat(stripped)
        except ValueError:
            raise ValidationError(
                field_name,
                f"invalid date format: '{stripped}' (expected YYYY-MM-DD)",
            )
    else:
        raise ValidationError(
            field_name,
            f"must be a date or ISO date string, got {type(value).__name__}",
        )

    if min_date is not None and date_val < min_date:
        raise ValidationError(
            field_name, f"must be on or after {min_date.isoformat()}"
        )

    if max_date is not None and date_val > max_date:
        raise ValidationError(
            field_name, f"must be on or before {max_date.isoformat()}"
        )

    return date_val


def validate_date_range(
    start_date,
    end_date,
    start_field: str = "start_date",
    end_field: str = "end_date",
) -> tuple:
    """Validate that start_date <= end_date.

    Both values are first validated individually. Returns
    ``(validated_start, validated_end)``.
    """
    validated_start = validate_date(start_date, start_field, required=True)
    validated_end = validate_date(end_date, end_field, required=True)

    if validated_start > validated_end:
        raise ValidationError(
            end_field,
            f"must be on or after {start_field} "
            f"({validated_start.isoformat()}), "
            f"got {validated_end.isoformat()}",
        )

    return (validated_start, validated_end)


def validate_email(
    value: str,
    field_name: str = "email",
    required: bool = True,
) -> Optional[str]:
    """Validate email format (simplified RFC 5322)."""
    if value is None:
        if required:
            raise ValidationError(field_name, "is required")
        return None

    if not isinstance(value, str):
        raise ValidationError(field_name, "must be a string")

    stripped = value.strip().lower()

    if not stripped:
        if required:
            raise ValidationError(field_name, "must not be empty")
        return None

    if len(stripped) > 254:
        raise ValidationError(field_name, "must be at most 254 characters")

    if not _EMAIL_RE.match(stripped):
        raise ValidationError(
            field_name, f"invalid email format: '{stripped}'"
        )

    return stripped


def validate_score(
    value,
    field_name: str,
    min_val: int = 1,
    max_val: int = 5,
) -> Optional[int]:
    """Validate a 1-5 score (e.g. risk probability / impact).

    Always required — a score of ``None`` is invalid.
    """
    return validate_integer(
        value, field_name, min_val=min_val, max_val=max_val, required=True
    )


def validate_percentage(
    value,
    field_name: str,
    required: bool = True,
) -> Optional[float]:
    """Validate a 0-100 percentage value."""
    return validate_float(
        value, field_name, min_val=0.0, max_val=100.0, required=required
    )


def validate_boolean(
    value,
    field_name: str,
    required: bool = True,
) -> Optional[bool]:
    """Validate a boolean value."""
    if value is None:
        if required:
            raise ValidationError(field_name, "is required")
        return None

    if not isinstance(value, bool):
        raise ValidationError(
            field_name, f"must be a boolean, got {type(value).__name__}"
        )

    return value


# ── Composite Validators ─────────────────────────────────────────────
# Convenience functions that validate all fields for a domain entity
# and return a dict of cleaned values ready for the repository layer.

def validate_task_create(
    title,
    task_type,
    priority,
    story_points=None,
    assignee=None,
    description=None,
) -> dict:
    """Validate all fields for task creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["title"] = validate_string(title, "title", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["task_type"] = validate_enum(task_type, TASK_TYPES, "task_type")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["priority"] = validate_enum(priority, PRIORITY_LEVELS, "priority")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["story_points"] = validate_integer(
            story_points, "story_points", min_val=0, max_val=100, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["assignee"] = validate_string(
            assignee, "assignee", max_length=200, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["description"] = validate_string(
            description, "description", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_risk_create(
    title,
    category,
    probability,
    impact,
    response_strategy=None,
    risk_proximity=None,
    description=None,
    mitigation_plan=None,
    contingency_plan=None,
    trigger_conditions=None,
    owner=None,
    response_owner=None,
) -> dict:
    """Validate all fields for risk creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["title"] = validate_string(title, "title", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["category"] = validate_enum(
            category, RISK_CATEGORIES, "category"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["probability"] = validate_score(probability, "probability")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["impact"] = validate_score(impact, "impact")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    # Auto-calculate risk_score
    if "probability" in cleaned and "impact" in cleaned:
        cleaned["risk_score"] = cleaned["probability"] * cleaned["impact"]

    try:
        cleaned["response_strategy"] = validate_enum(
            response_strategy,
            RISK_RESPONSE_STRATEGIES,
            "response_strategy",
            required=False,
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["risk_proximity"] = validate_enum(
            risk_proximity, RISK_PROXIMITY, "risk_proximity", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["description"] = validate_string(
            description, "description", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["mitigation_plan"] = validate_string(
            mitigation_plan, "mitigation_plan", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["contingency_plan"] = validate_string(
            contingency_plan, "contingency_plan", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["trigger_conditions"] = validate_string(
            trigger_conditions,
            "trigger_conditions",
            max_length=2000,
            required=False,
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["owner"] = validate_string(
            owner, "owner", max_length=200, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["response_owner"] = validate_string(
            response_owner, "response_owner", max_length=200, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_sprint_create(
    name,
    start_date,
    end_date,
    capacity_points=None,
    goal=None,
) -> dict:
    """Validate all fields for sprint creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["name"] = validate_string(name, "name", max_length=100)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        start, end = validate_date_range(
            start_date, end_date, "start_date", "end_date"
        )
        cleaned["start_date"] = start
        cleaned["end_date"] = end
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["capacity_points"] = validate_integer(
            capacity_points,
            "capacity_points",
            min_val=0,
            max_val=999,
            required=False,
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["goal"] = validate_string(
            goal, "goal", max_length=1000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_project_create(
    name,
    delivery_method,
    status,
    health,
    start_date,
    owner,
    description=None,
    target_date=None,
    budget_total=None,
) -> dict:
    """Validate all fields for project creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["name"] = validate_string(name, "name", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["delivery_method"] = validate_enum(
            delivery_method, DELIVERY_METHODS, "delivery_method"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["status"] = validate_enum(
            status, PROJECT_STATUSES, "status"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["health"] = validate_enum(health, HEALTH_VALUES, "health")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["start_date"] = validate_date(start_date, "start_date")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["owner"] = validate_string(owner, "owner", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["description"] = validate_string(
            description, "description", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["target_date"] = validate_date(
            target_date, "target_date", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    # If both dates present, ensure target >= start
    if cleaned.get("start_date") and cleaned.get("target_date"):
        if cleaned["target_date"] < cleaned["start_date"]:
            result.add_error(
                "target_date",
                f"must be on or after start_date ({cleaned['start_date'].isoformat()})",
            )

    try:
        cleaned["budget_total"] = validate_float(
            budget_total, "budget_total", min_val=0.0, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_charter_create(
    project_name,
    business_case,
    objectives,
    scope_in,
    scope_out=None,
    stakeholders=None,
    success_criteria=None,
    risks=None,
    budget=None,
    timeline=None,
    delivery_method=None,
    description=None,
) -> dict:
    """Validate all fields for charter creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["project_name"] = validate_string(
            project_name, "project_name", max_length=200
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["business_case"] = validate_string(
            business_case, "business_case", max_length=5000
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["objectives"] = validate_string(
            objectives, "objectives", max_length=5000
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["scope_in"] = validate_string(
            scope_in, "scope_in", max_length=5000
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["scope_out"] = validate_string(
            scope_out, "scope_out", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["stakeholders"] = validate_string(
            stakeholders, "stakeholders", max_length=2000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["success_criteria"] = validate_string(
            success_criteria, "success_criteria", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["risks"] = validate_string(
            risks, "risks", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["budget"] = validate_string(
            budget, "budget", max_length=100, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["timeline"] = validate_string(
            timeline, "timeline", max_length=200, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["delivery_method"] = validate_enum(
            delivery_method, DELIVERY_METHODS, "delivery_method"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["description"] = validate_string(
            description, "description", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_retro_item_create(
    category,
    body,
    author=None,
) -> dict:
    """Validate all fields for retro item creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["category"] = validate_enum(
            category, RETRO_CATEGORIES, "category"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["body"] = validate_string(body, "body", max_length=2000)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["author"] = validate_string(
            author, "author", max_length=200, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_phase_create(
    name,
    phase_type,
    delivery_method,
    phase_order,
    start_date=None,
    end_date=None,
) -> dict:
    """Validate all fields for phase creation. Returns cleaned data dict."""
    result = ValidationResult()
    cleaned = {}

    try:
        cleaned["name"] = validate_string(name, "name", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["phase_type"] = validate_enum(
            phase_type, PHASE_TYPES, "phase_type"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["delivery_method"] = validate_enum(
            delivery_method, DELIVERY_METHODS, "delivery_method"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["phase_order"] = validate_integer(
            phase_order, "phase_order", min_val=1, max_val=99
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["start_date"] = validate_date(
            start_date, "start_date", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["end_date"] = validate_date(
            end_date, "end_date", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    # If both dates present, ensure end >= start
    if cleaned.get("start_date") and cleaned.get("end_date"):
        if cleaned["end_date"] < cleaned["start_date"]:
            result.add_error(
                "end_date",
                f"must be on or after start_date ({cleaned['start_date'].isoformat()})",
            )

    result.raise_if_invalid()
    return cleaned


def validate_gate_create(
    name,
    criteria=None,
) -> dict:
    """Validate all fields for gate creation. Returns cleaned data dict."""
    result = ValidationResult()
    cleaned = {}

    try:
        cleaned["name"] = validate_string(name, "name", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["criteria"] = validate_string(
            criteria, "criteria", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_dependency_create(
    source_project_id,
    target_project_id,
    dependency_type,
    risk_level,
    description=None,
    status=None,
) -> dict:
    """Validate all fields for dependency creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["source_project_id"] = validate_string(
            source_project_id, "source_project_id", max_length=50
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["target_project_id"] = validate_string(
            target_project_id, "target_project_id", max_length=50
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    # Source and target must be different
    if (cleaned.get("source_project_id") and cleaned.get("target_project_id")
            and cleaned["source_project_id"] == cleaned["target_project_id"]):
        result.add_error(
            "target_project_id",
            "target project must be different from source project",
        )

    try:
        cleaned["dependency_type"] = validate_enum(
            dependency_type, DEPENDENCY_TYPES, "dependency_type"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["risk_level"] = validate_enum(
            risk_level, DEPENDENCY_RISK_LEVELS, "risk_level"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["description"] = validate_string(
            description, "description", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["status"] = validate_enum(
            status, DEPENDENCY_STATUSES, "status", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_deliverable_create(
    name,
    status,
    owner=None,
    due_date=None,
    description=None,
    artifact_url=None,
) -> dict:
    """Validate all fields for deliverable creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["name"] = validate_string(name, "name", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["status"] = validate_enum(
            status, DELIVERABLE_STATUSES, "status", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["owner"] = validate_string(
            owner, "owner", max_length=200, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["due_date"] = validate_date(
            due_date, "due_date", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["description"] = validate_string(
            description, "description", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["artifact_url"] = validate_string(
            artifact_url, "artifact_url", max_length=2000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_time_entry_create(
    task_id,
    user_id,
    hours,
    work_date,
    notes=None,
) -> dict:
    """Validate all fields for time entry creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["task_id"] = validate_string(task_id, "task_id", max_length=50)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["user_id"] = validate_string(user_id, "user_id", max_length=50)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["hours"] = validate_float(
            hours, "hours", min_val=0.01, max_val=24.0, required=True
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["work_date"] = validate_date(work_date, "work_date", required=True)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["notes"] = validate_string(
            notes, "notes", max_length=2000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_comment_create(
    body,
    author=None,
) -> dict:
    """Validate all fields for comment creation. Returns cleaned data dict."""
    result = ValidationResult()

    cleaned = {}

    try:
        cleaned["body"] = validate_string(body, "body", max_length=5000)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["author"] = validate_string(
            author, "author", max_length=200, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned


def validate_assignment_create(
    project_id,
    user_id,
    project_role,
    allocation_pct,
    start_date=None,
    end_date=None,
) -> dict:
    """Validate all fields for project_team assignment creation. Returns cleaned data dict."""
    result = ValidationResult()
    cleaned = {}

    try:
        cleaned["project_id"] = validate_uuid(project_id, "project_id")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["user_id"] = validate_uuid(user_id, "user_id")
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["project_role"] = validate_enum(
            project_role, PROJECT_ROLES, "project_role"
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["allocation_pct"] = validate_integer(
            allocation_pct, "allocation_pct", min_val=0, max_val=100
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["start_date"] = validate_date(
            start_date, "start_date", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["end_date"] = validate_date(
            end_date, "end_date", required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    # If both dates present, ensure end >= start
    if cleaned.get("start_date") and cleaned.get("end_date"):
        if cleaned["end_date"] < cleaned["start_date"]:
            result.add_error(
                "end_date",
                f"must be on or after start_date ({cleaned['start_date'].isoformat()})",
            )

    result.raise_if_invalid()
    return cleaned


def validate_portfolio_create(
    name,
    owner,
    description=None,
    strategic_priority=None,
    department_id=None,
) -> dict:
    """Validate all fields for portfolio creation. Returns cleaned data dict."""
    result = ValidationResult()
    cleaned = {}

    try:
        cleaned["name"] = validate_string(name, "name", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["owner"] = validate_string(owner, "owner", max_length=200)
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["description"] = validate_string(
            description, "description", max_length=5000, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["strategic_priority"] = validate_string(
            strategic_priority, "strategic_priority", max_length=500, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    try:
        cleaned["department_id"] = validate_string(
            department_id, "department_id", max_length=50, required=False
        )
    except ValidationError as exc:
        result.add_error(exc.field, exc.message)

    result.raise_if_invalid()
    return cleaned
