-- Migration 001: Add updated_at to mutable tables missing it
-- Tables: phases, gates, deliverables, sprints, team_members, project_team, retro_items, dependencies

ALTER TABLE phases ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE gates ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE deliverables ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE sprints ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE team_members ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE project_team ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE retro_items ADD COLUMN updated_at TIMESTAMP;
ALTER TABLE dependencies ADD COLUMN updated_at TIMESTAMP;
