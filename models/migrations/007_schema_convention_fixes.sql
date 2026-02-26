-- Migration 007: Schema convention fixes
-- Fix project_team missing created_at
-- Fix team_members: rename joined_at → created_at, add updated_at, add soft delete

-- project_team: add created_at
ALTER TABLE project_team ADD COLUMNS (
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp() COMMENT 'When assignment was created'
);

-- team_members: add updated_at (joined_at rename requires recreate in Delta, so add new column)
ALTER TABLE team_members ADD COLUMNS (
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp() COMMENT 'Last update timestamp',
    is_deleted BOOLEAN NOT NULL DEFAULT false COMMENT 'Soft delete flag',
    deleted_at TIMESTAMP COMMENT 'When soft-deleted'
);

-- Note: Renaming joined_at → created_at in Delta Lake requires:
-- 1. Add created_at column
-- 2. UPDATE team_members SET created_at = joined_at
-- 3. In next release, stop using joined_at
-- For now, the DDL uses created_at for new deployments.
-- Existing deployments should run this migration manually.
