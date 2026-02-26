-- Migration 001: Add updated_at NOT NULL DEFAULT to mutable tables missing it
-- Tables: phases, gates, deliverables, sprints, team_members, project_team, retro_items, dependencies
-- Also fixes comments.updated_at to NOT NULL DEFAULT

ALTER TABLE phases ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();
ALTER TABLE gates ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();
ALTER TABLE deliverables ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();
ALTER TABLE sprints ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();
ALTER TABLE team_members ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();
ALTER TABLE project_team ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();
ALTER TABLE retro_items ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();
ALTER TABLE dependencies ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp();

-- Fix comments.updated_at: add NOT NULL constraint and default
ALTER TABLE comments ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE comments ALTER COLUMN updated_at SET DEFAULT current_timestamp();
