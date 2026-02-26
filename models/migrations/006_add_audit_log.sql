-- Migration 006: Add audit_log table
-- Centralized audit trail for all entity changes

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id        STRING      NOT NULL    COMMENT 'PK — UUID',
    user_email      STRING      NOT NULL    COMMENT 'Who performed the action',
    action          STRING      NOT NULL    COMMENT 'create | update | delete | approve | reject',
    entity_type     STRING      NOT NULL    COMMENT 'task | project | charter | risk | sprint | etc.',
    entity_id       STRING      NOT NULL    COMMENT 'PK of the affected entity',
    field_changed   STRING                  COMMENT 'Which field changed (null for create/delete)',
    old_value       STRING                  COMMENT 'Previous value',
    new_value       STRING                  COMMENT 'New value',
    details         STRING                  COMMENT 'JSON blob for complex changes',
    created_at      TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),

    CONSTRAINT pk_audit_log PRIMARY KEY (audit_id)
)
COMMENT 'Centralized audit trail — all entity mutations logged here';
