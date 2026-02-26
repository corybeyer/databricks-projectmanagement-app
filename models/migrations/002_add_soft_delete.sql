-- Migration 002: Add soft delete fields to all mutable tables
-- Adds is_deleted (BOOLEAN NOT NULL DEFAULT false) and deleted_at (TIMESTAMP)
-- Excludes immutable/append-only tables: status_transitions, time_entries, team_members

ALTER TABLE portfolios ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE portfolios ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE projects ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE projects ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE project_charters ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE project_charters ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE phases ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE phases ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE gates ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE gates ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE deliverables ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE deliverables ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE sprints ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE sprints ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE tasks ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE tasks ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE comments ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE comments ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE risks ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE risks ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE retro_items ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE retro_items ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE dependencies ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE dependencies ADD COLUMN deleted_at TIMESTAMP;

ALTER TABLE project_team ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE project_team ADD COLUMN deleted_at TIMESTAMP;
