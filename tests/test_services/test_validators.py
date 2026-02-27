"""Tests for input validators."""
import os
os.environ["USE_SAMPLE_DATA"] = "true"

import pytest
from datetime import date
from utils.validators import (
    ValidationError, ValidationResult,
    validate_string, validate_enum, validate_integer, validate_float,
    validate_date, validate_date_range, validate_email, validate_uuid,
    validate_score, validate_percentage, validate_boolean,
    validate_task_create, validate_risk_create, validate_sprint_create,
    validate_project_create, validate_charter_create, validate_portfolio_create,
    TASK_TYPES, PRIORITY_LEVELS, RISK_CATEGORIES, DELIVERY_METHODS,
    PROJECT_STATUSES, HEALTH_VALUES,
)


# ── Individual Validators ──────────────────────────────────────────────


class TestValidateString:
    def test_valid_string(self):
        assert validate_string("hello", "field") == "hello"

    def test_strips_whitespace(self):
        assert validate_string("  hello  ", "field") == "hello"

    def test_empty_string_required(self):
        with pytest.raises(ValidationError):
            validate_string("", "field")

    def test_none_required(self):
        with pytest.raises(ValidationError):
            validate_string(None, "field")

    def test_none_optional(self):
        assert validate_string(None, "field", required=False) is None

    def test_empty_optional(self):
        assert validate_string("", "field", required=False) is None

    def test_max_length(self):
        with pytest.raises(ValidationError):
            validate_string("a" * 201, "field", max_length=200)

    def test_not_a_string(self):
        with pytest.raises(ValidationError):
            validate_string(123, "field")


class TestValidateEnum:
    def test_valid_enum(self):
        assert validate_enum("story", TASK_TYPES, "type") == "story"

    def test_case_insensitive(self):
        assert validate_enum("STORY", TASK_TYPES, "type") == "story"

    def test_invalid_value(self):
        with pytest.raises(ValidationError):
            validate_enum("not_valid", TASK_TYPES, "type")

    def test_none_required(self):
        with pytest.raises(ValidationError):
            validate_enum(None, TASK_TYPES, "type")

    def test_none_optional(self):
        assert validate_enum(None, TASK_TYPES, "type", required=False) is None

    def test_empty_required(self):
        with pytest.raises(ValidationError):
            validate_enum("", TASK_TYPES, "type")


class TestValidateInteger:
    def test_valid_int(self):
        assert validate_integer(5, "field") == 5

    def test_string_int(self):
        assert validate_integer("5", "field") == 5

    def test_min_val(self):
        with pytest.raises(ValidationError):
            validate_integer(-1, "field", min_val=0)

    def test_max_val(self):
        with pytest.raises(ValidationError):
            validate_integer(101, "field", max_val=100)

    def test_none_required(self):
        with pytest.raises(ValidationError):
            validate_integer(None, "field")

    def test_none_optional(self):
        assert validate_integer(None, "field", required=False) is None

    def test_invalid_string(self):
        with pytest.raises(ValidationError):
            validate_integer("abc", "field")

    def test_boolean_rejected(self):
        with pytest.raises(ValidationError):
            validate_integer(True, "field")


class TestValidateFloat:
    def test_valid_float(self):
        assert validate_float(3.14, "field") == 3.14

    def test_string_float(self):
        assert validate_float("3.14", "field") == 3.14

    def test_min_val(self):
        with pytest.raises(ValidationError):
            validate_float(-1.0, "field", min_val=0.0)

    def test_none_optional(self):
        assert validate_float(None, "field", required=False) is None


class TestValidateDate:
    def test_valid_iso_string(self):
        result = validate_date("2026-03-01", "field")
        assert result == date(2026, 3, 1)

    def test_valid_date_object(self):
        d = date(2026, 3, 1)
        assert validate_date(d, "field") == d

    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_date("03/01/2026", "field")

    def test_none_required(self):
        with pytest.raises(ValidationError):
            validate_date(None, "field")

    def test_none_optional(self):
        assert validate_date(None, "field", required=False) is None

    def test_empty_string_required(self):
        with pytest.raises(ValidationError):
            validate_date("", "field")


class TestValidateDateRange:
    def test_valid_range(self):
        start, end = validate_date_range("2026-03-01", "2026-03-14")
        assert start < end

    def test_same_day(self):
        start, end = validate_date_range("2026-03-01", "2026-03-01")
        assert start == end

    def test_end_before_start(self):
        with pytest.raises(ValidationError):
            validate_date_range("2026-03-14", "2026-03-01")


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("test@example.com", "email") == "test@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            validate_email("not-an-email", "email")

    def test_none_optional(self):
        assert validate_email(None, "email", required=False) is None


class TestValidateUuid:
    def test_valid_short_id(self):
        assert validate_uuid("prj-001", "id") == "prj-001"

    def test_valid_uuid(self):
        result = validate_uuid("12345678-1234-1234-1234-123456789012", "id")
        assert result == "12345678-1234-1234-1234-123456789012"

    def test_invalid_format(self):
        with pytest.raises(ValidationError):
            validate_uuid("not valid at all!", "id")

    def test_none(self):
        with pytest.raises(ValidationError):
            validate_uuid(None, "id")


class TestValidateScore:
    def test_valid_score(self):
        assert validate_score(3, "field") == 3

    def test_below_range(self):
        with pytest.raises(ValidationError):
            validate_score(0, "field")

    def test_above_range(self):
        with pytest.raises(ValidationError):
            validate_score(6, "field")


class TestValidatePercentage:
    def test_valid(self):
        assert validate_percentage(50.0, "field") == 50.0

    def test_below_zero(self):
        with pytest.raises(ValidationError):
            validate_percentage(-1.0, "field")

    def test_above_100(self):
        with pytest.raises(ValidationError):
            validate_percentage(101.0, "field")


class TestValidateBoolean:
    def test_true(self):
        assert validate_boolean(True, "field") is True

    def test_false(self):
        assert validate_boolean(False, "field") is False

    def test_not_bool(self):
        with pytest.raises(ValidationError):
            validate_boolean("true", "field")

    def test_none_optional(self):
        assert validate_boolean(None, "field", required=False) is None


# ── Composite Validators ───────────────────────────────────────────────


class TestValidateTaskCreate:
    def test_valid_task(self):
        cleaned = validate_task_create(
            title="My Task", task_type="story", priority="medium"
        )
        assert cleaned["title"] == "My Task"
        assert cleaned["task_type"] == "story"
        assert cleaned["priority"] == "medium"

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            validate_task_create(title="", task_type="story", priority="medium")

    def test_invalid_task_type(self):
        with pytest.raises(ValidationError):
            validate_task_create(title="Task", task_type="invalid", priority="medium")

    def test_with_story_points(self):
        cleaned = validate_task_create(
            title="Task", task_type="story", priority="medium",
            story_points="5",
        )
        assert cleaned["story_points"] == 5

    def test_story_points_out_of_range(self):
        with pytest.raises(ValidationError):
            validate_task_create(
                title="Task", task_type="story", priority="medium",
                story_points="200",
            )


class TestValidateRiskCreate:
    def test_valid_risk(self):
        cleaned = validate_risk_create(
            title="Risk", category="technical",
            probability="3", impact="4",
        )
        assert cleaned["title"] == "Risk"
        assert cleaned["risk_score"] == 12

    def test_missing_title(self):
        with pytest.raises(ValidationError):
            validate_risk_create(
                title="", category="technical",
                probability="3", impact="4",
            )

    def test_probability_out_of_range(self):
        with pytest.raises(ValidationError):
            validate_risk_create(
                title="Risk", category="technical",
                probability="6", impact="4",
            )


class TestValidateSprintCreate:
    def test_valid_sprint(self):
        cleaned = validate_sprint_create(
            name="Sprint 1",
            start_date="2026-03-01",
            end_date="2026-03-14",
        )
        assert cleaned["name"] == "Sprint 1"
        assert cleaned["start_date"] == date(2026, 3, 1)
        assert cleaned["end_date"] == date(2026, 3, 14)

    def test_end_before_start(self):
        with pytest.raises(ValidationError):
            validate_sprint_create(
                name="Sprint 1",
                start_date="2026-03-14",
                end_date="2026-03-01",
            )


class TestValidateProjectCreate:
    def test_valid_project(self):
        cleaned = validate_project_create(
            name="Project", delivery_method="agile",
            status="planning", health="green",
            start_date="2026-03-01", owner="Test",
        )
        assert cleaned["name"] == "Project"
        assert cleaned["delivery_method"] == "agile"

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            validate_project_create(
                name="", delivery_method="agile",
                status="planning", health="green",
                start_date="2026-03-01", owner="Test",
            )


class TestValidateCharterCreate:
    def test_valid_charter(self):
        cleaned = validate_charter_create(
            project_name="Charter", business_case="Business case",
            objectives="Objectives", scope_in="In scope",
            delivery_method="agile",
        )
        assert cleaned["project_name"] == "Charter"

    def test_missing_business_case(self):
        with pytest.raises(ValidationError):
            validate_charter_create(
                project_name="Charter", business_case="",
                objectives="Objectives", scope_in="In scope",
                delivery_method="agile",
            )


class TestValidatePortfolioCreate:
    def test_valid_portfolio(self):
        cleaned = validate_portfolio_create(
            name="Portfolio", owner="Owner",
        )
        assert cleaned["name"] == "Portfolio"
        assert cleaned["owner"] == "Owner"

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            validate_portfolio_create(name="", owner="Owner")

    def test_missing_owner(self):
        with pytest.raises(ValidationError):
            validate_portfolio_create(name="Portfolio", owner="")


class TestValidationResult:
    def test_empty_is_valid(self):
        vr = ValidationResult()
        assert vr.is_valid is True

    def test_with_error_is_invalid(self):
        vr = ValidationResult()
        vr.add_error("field", "error message")
        assert vr.is_valid is False

    def test_raise_if_invalid(self):
        vr = ValidationResult()
        vr.add_error("field1", "msg1")
        vr.add_error("field2", "msg2")
        with pytest.raises(ValidationError) as exc_info:
            vr.raise_if_invalid()
        assert "field1" in str(exc_info.value)
