-- Migration 003: Add per-user activity tracking columns
-- Add created_by, updated_by, deleted_by to all mutable tables
-- Tables: portfolios, projects, project_charters, phases, gates,
--         deliverables, sprints, tasks, comments, time_entries,
--         risks, retro_items, dependencies

ALTER TABLE portfolios ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE projects ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE project_charters ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE phases ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE gates ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE deliverables ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE sprints ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE tasks ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE comments ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE time_entries ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE risks ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE retro_items ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);

ALTER TABLE dependencies ADD COLUMNS (
    created_by STRING COMMENT 'User email who created',
    updated_by STRING COMMENT 'User email who last updated',
    deleted_by STRING COMMENT 'User email who soft-deleted'
);
