-- Migration 004: Add departments table and department_id to portfolios/team_members
-- Phase 0.1 — Multi-Department Hierarchy
-- Run against: workspace.project_management

USE workspace.project_management;

-- 1. Create departments table
CREATE TABLE IF NOT EXISTS departments (
    department_id   STRING      NOT NULL    COMMENT 'PK — UUID',
    name            STRING      NOT NULL    COMMENT 'Department display name',
    description     STRING                  COMMENT 'Department description',
    parent_dept_id  STRING                  COMMENT 'FK → departments (self-ref for hierarchy)',
    head            STRING                  COMMENT 'Department head user_id',
    created_at      TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    updated_at      TIMESTAMP   NOT NULL    DEFAULT current_timestamp(),
    created_by      STRING                  COMMENT 'User email who created',
    updated_by      STRING                  COMMENT 'User email who last updated',
    deleted_by      STRING                  COMMENT 'User email who soft-deleted',
    is_deleted      BOOLEAN     NOT NULL    DEFAULT false,
    deleted_at      TIMESTAMP                             COMMENT 'When soft-deleted',

    CONSTRAINT pk_departments PRIMARY KEY (department_id)
)
COMMENT 'Organizational departments — multi-department hierarchy'
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true');

-- 2. Add department_id to portfolios
ALTER TABLE portfolios ADD COLUMN department_id STRING NOT NULL COMMENT 'FK → departments';
ALTER TABLE portfolios ADD CONSTRAINT fk_portfolios_department FOREIGN KEY (department_id) REFERENCES departments(department_id);

-- 3. Add department_id to team_members
ALTER TABLE team_members ADD COLUMN department_id STRING NOT NULL COMMENT 'FK → departments';
ALTER TABLE team_members ADD CONSTRAINT fk_team_members_department FOREIGN KEY (department_id) REFERENCES departments(department_id);
