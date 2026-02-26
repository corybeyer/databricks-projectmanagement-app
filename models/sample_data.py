"""
Sample Data — Local Development Fallback
==========================================
Returns realistic sample data when not connected to Databricks.
Each function returns a pd.DataFrame matching the UC table schema.
"""

import pandas as pd


def get_portfolios() -> pd.DataFrame:
    return pd.DataFrame([
        {"portfolio_id": "pf-001", "name": "Data Platform Modernization", "owner": "Cory S.",
         "status": "active", "health": "yellow", "project_count": 5,
         "avg_completion": 58, "total_spent": 792000, "total_budget": 1100000},
        {"portfolio_id": "pf-002", "name": "Financial Reporting & Analytics", "owner": "Cory S.",
         "status": "active", "health": "green", "project_count": 4,
         "avg_completion": 64, "total_spent": 483800, "total_budget": 820000},
        {"portfolio_id": "pf-003", "name": "Self-Service & Applications", "owner": "Cory S.",
         "status": "active", "health": "green", "project_count": 3,
         "avg_completion": 42, "total_spent": 182400, "total_budget": 480000},
    ])


def get_portfolio_projects() -> pd.DataFrame:
    return pd.DataFrame([
        {"project_id": "prj-001", "name": "Unity Catalog Migration", "status": "active",
         "delivery_method": "hybrid", "pct_complete": 55, "current_phase_name": "Build",
         "health": "yellow", "budget_total": 420000, "budget_spent": 302400,
         "active_sprint_name": "Sprint 4", "start_date": "2026-01-06", "target_date": "2026-08-01",
         "portfolio_name": "Data Platform Modernization"},
        {"project_id": "prj-002", "name": "DLT Pipeline Framework", "status": "active",
         "delivery_method": "agile", "pct_complete": 72, "current_phase_name": "Build",
         "health": "green", "budget_total": 320000, "budget_spent": 230400,
         "active_sprint_name": "Sprint 6", "start_date": "2026-01-13", "target_date": "2026-06-15",
         "portfolio_name": "Data Platform Modernization"},
        {"project_id": "prj-003", "name": "Secrets Management Rollout", "status": "active",
         "delivery_method": "waterfall", "pct_complete": 85, "current_phase_name": "UAT",
         "health": "green", "budget_total": 80000, "budget_spent": 68000,
         "active_sprint_name": None, "start_date": "2025-11-01", "target_date": "2026-03-15",
         "portfolio_name": "Data Platform Modernization"},
    ])


def get_project_charter() -> pd.DataFrame:
    return pd.DataFrame([
        {"charter_id": "ch-001", "project_id": "prj-001",
         "project_name": "Unity Catalog Migration",
         "business_case": "Migrate legacy Hive metastore to Unity Catalog for centralized governance, lineage tracking, and cross-workspace data sharing.",
         "objectives": "1. Migrate 100% of production tables to UC by Q2\n2. Implement domain-driven schema design\n3. Enable row-level security for Finance data\n4. Establish automated lineage tracking",
         "scope_in": "All production Databricks workspaces, Bronze/Silver/Gold layers, access policies, secrets management integration",
         "scope_out": "Legacy on-prem SQL Server databases, third-party tool migrations, Power BI semantic model changes",
         "stakeholders": "CIO (Sponsor), VP Data (Owner), Finance Dir (Key User), IT Security (Reviewer)",
         "success_criteria": "Zero data loss during migration, <2hr downtime per workspace, all access policies replicated, UAT sign-off from Finance",
         "risks": "Resource contention with DLT project, SAP BW schema changes mid-migration, team capacity constraints",
         "budget": "$420,000", "timeline": "Jan 2026 — Aug 2026",
         "delivery_method": "Hybrid — Waterfall phases with Agile sprint execution",
         "approved_by": "VP Data & Analytics", "approved_date": "2025-12-15"},
    ])


def get_sprints() -> pd.DataFrame:
    return pd.DataFrame([
        {"sprint_id": "sp-001", "name": "Sprint 1", "status": "closed",
         "start_date": "2026-01-20", "end_date": "2026-01-31",
         "total_points": 26, "done_points": 24, "capacity_points": 28},
        {"sprint_id": "sp-002", "name": "Sprint 2", "status": "closed",
         "start_date": "2026-02-03", "end_date": "2026-02-14",
         "total_points": 30, "done_points": 28, "capacity_points": 30},
        {"sprint_id": "sp-003", "name": "Sprint 3", "status": "closed",
         "start_date": "2026-02-17", "end_date": "2026-02-28",
         "total_points": 32, "done_points": 32, "capacity_points": 32},
        {"sprint_id": "sp-004", "name": "Sprint 4", "status": "active",
         "start_date": "2026-03-02", "end_date": "2026-03-13",
         "total_points": 34, "done_points": 21, "capacity_points": 34},
    ])


def get_tasks() -> pd.DataFrame:
    return pd.DataFrame([
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "status": "done", "story_points": 8, "assignee_name": "Chris J.", "priority": "high"},
        {"task_id": "t-002", "title": "DLT pipeline — Cost Centers", "task_type": "story",
         "status": "in_progress", "story_points": 8, "assignee_name": "Chris J.", "priority": "high"},
        {"task_id": "t-003", "title": "SQL Server sync job", "task_type": "story",
         "status": "in_progress", "story_points": 5, "assignee_name": "Cory S.", "priority": "medium"},
        {"task_id": "t-004", "title": "UAT comparison notebook", "task_type": "task",
         "status": "review", "story_points": 3, "assignee_name": "Chris J.", "priority": "medium"},
        {"task_id": "t-005", "title": "Bronze→Silver GL mapping", "task_type": "story",
         "status": "todo", "story_points": 5, "assignee_name": "Cory S.", "priority": "high"},
        {"task_id": "t-006", "title": "Secrets vault integration", "task_type": "task",
         "status": "todo", "story_points": 3, "assignee_name": None, "priority": "medium"},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "status": "done", "story_points": 5, "assignee_name": "Anna K.", "priority": "high"},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "status": "done", "story_points": 2, "assignee_name": "Cory S.", "priority": "medium"},
    ])


def get_risks() -> pd.DataFrame:
    return pd.DataFrame([
        {"risk_id": "r-001", "project_id": "prj-001", "portfolio_id": "pf-001",
         "title": "SAP BW schema changes during migration",
         "project_name": "Unity Catalog Migration", "portfolio_name": "Data Platform Modernization",
         "category": "scope", "probability": 4, "impact": 4, "risk_score": 16,
         "status": "mitigating", "owner": "Cory S."},
        {"risk_id": "r-002", "project_id": "prj-002", "portfolio_id": "pf-001",
         "title": "DLT framework version upgrade mid-sprint",
         "project_name": "DLT Pipeline Framework", "portfolio_name": "Data Platform Modernization",
         "category": "technical", "probability": 3, "impact": 3, "risk_score": 9,
         "status": "open", "owner": "Chris J."},
    ])


def get_resource_allocations() -> pd.DataFrame:
    return pd.DataFrame([
        {"user_id": "u-001", "display_name": "Cory S.", "role": "lead",
         "project_name": "Unity Catalog Migration", "project_id": "prj-001",
         "task_count": 3, "points_assigned": 13, "points_done": 2, "allocation_pct": 60},
        {"user_id": "u-001", "display_name": "Cory S.", "role": "lead",
         "project_name": "DLT Pipeline Framework", "project_id": "prj-002",
         "task_count": 1, "points_assigned": 5, "points_done": 3, "allocation_pct": 30},
        {"user_id": "u-002", "display_name": "Chris J.", "role": "engineer",
         "project_name": "Unity Catalog Migration", "project_id": "prj-001",
         "task_count": 3, "points_assigned": 19, "points_done": 8, "allocation_pct": 80},
        {"user_id": "u-003", "display_name": "Anna K.", "role": "analyst",
         "project_name": "DLT Pipeline Framework", "project_id": "prj-002",
         "task_count": 1, "points_assigned": 5, "points_done": 5, "allocation_pct": 50},
        {"user_id": "u-003", "display_name": "Anna K.", "role": "analyst",
         "project_name": "Secrets Management Rollout", "project_id": "prj-003",
         "task_count": 2, "points_assigned": 6, "points_done": 4, "allocation_pct": 40},
    ])


def get_project_detail() -> pd.DataFrame:
    return pd.DataFrame([
        {"project_id": "prj-001", "name": "Unity Catalog Migration", "status": "active",
         "delivery_method": "hybrid", "pct_complete": 55, "current_phase_name": "Build",
         "health": "yellow", "budget_total": 420000, "budget_spent": 302400,
         "portfolio_name": "Data Platform Modernization", "portfolio_id": "pf-001",
         "start_date": "2026-01-06", "target_date": "2026-08-01",
         "priority_rank": 1, "description": "Migrate legacy Hive metastore to Unity Catalog."},
    ])


def get_project_phases() -> pd.DataFrame:
    return pd.DataFrame([
        {"phase_id": "ph-001", "name": "Initiation", "phase_type": "initiation",
         "delivery_method": "waterfall", "status": "done", "pct_complete": 100,
         "start_date": "2026-01-06", "end_date": "2026-01-17", "phase_order": 1,
         "task_count": 4, "done_count": 4},
        {"phase_id": "ph-002", "name": "Planning", "phase_type": "planning",
         "delivery_method": "waterfall", "status": "done", "pct_complete": 100,
         "start_date": "2026-01-20", "end_date": "2026-02-07", "phase_order": 2,
         "task_count": 6, "done_count": 6},
        {"phase_id": "ph-003", "name": "Build", "phase_type": "execution",
         "delivery_method": "agile", "status": "in_progress", "pct_complete": 55,
         "start_date": "2026-02-10", "end_date": "2026-05-29", "phase_order": 3,
         "task_count": 18, "done_count": 10},
        {"phase_id": "ph-004", "name": "UAT", "phase_type": "testing",
         "delivery_method": "waterfall", "status": "not_started", "pct_complete": 0,
         "start_date": "2026-06-01", "end_date": "2026-07-10", "phase_order": 4,
         "task_count": 0, "done_count": 0},
        {"phase_id": "ph-005", "name": "Deployment", "phase_type": "deployment",
         "delivery_method": "waterfall", "status": "not_started", "pct_complete": 0,
         "start_date": "2026-07-13", "end_date": "2026-08-01", "phase_order": 5,
         "task_count": 0, "done_count": 0},
    ])


def get_velocity() -> pd.DataFrame:
    return pd.DataFrame([
        {"sprint_name": "Sprint 1", "committed_points": 26, "completed_points": 24,
         "capacity_points": 28, "start_date": "2026-01-20", "end_date": "2026-01-31"},
        {"sprint_name": "Sprint 2", "committed_points": 30, "completed_points": 28,
         "capacity_points": 30, "start_date": "2026-02-03", "end_date": "2026-02-14"},
        {"sprint_name": "Sprint 3", "committed_points": 32, "completed_points": 32,
         "capacity_points": 32, "start_date": "2026-02-17", "end_date": "2026-02-28"},
    ])


def get_burndown() -> pd.DataFrame:
    return pd.DataFrame([
        {"burn_date": "2026-03-02", "remaining_points": 34, "total_points": 34},
        {"burn_date": "2026-03-03", "remaining_points": 32, "total_points": 34},
        {"burn_date": "2026-03-04", "remaining_points": 29, "total_points": 34},
        {"burn_date": "2026-03-05", "remaining_points": 27, "total_points": 34},
        {"burn_date": "2026-03-06", "remaining_points": 27, "total_points": 34},
        {"burn_date": "2026-03-07", "remaining_points": 25, "total_points": 34},
        {"burn_date": "2026-03-08", "remaining_points": 25, "total_points": 34},
        {"burn_date": "2026-03-09", "remaining_points": 21, "total_points": 34},
        {"burn_date": "2026-03-10", "remaining_points": 18, "total_points": 34},
        {"burn_date": "2026-03-11", "remaining_points": 13, "total_points": 34},
    ])


def get_gate_status() -> pd.DataFrame:
    return pd.DataFrame([
        {"gate_id": "g-001", "phase_id": "ph-001", "phase_name": "Initiation",
         "status": "approved", "gate_order": 1, "decided_by": "VP Data",
         "decided_at": "2026-01-17"},
        {"gate_id": "g-002", "phase_id": "ph-002", "phase_name": "Planning",
         "status": "approved", "gate_order": 2, "decided_by": "VP Data",
         "decided_at": "2026-02-07"},
        {"gate_id": "g-003", "phase_id": "ph-003", "phase_name": "Build",
         "status": "pending", "gate_order": 3, "decided_by": None,
         "decided_at": None},
        {"gate_id": "g-004", "phase_id": "ph-004", "phase_name": "UAT",
         "status": "pending", "gate_order": 4, "decided_by": None,
         "decided_at": None},
    ])


def get_cycle_times() -> pd.DataFrame:
    return pd.DataFrame([
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "from_status": "todo", "hours_in_status": 4},
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "from_status": "in_progress", "hours_in_status": 32},
        {"task_id": "t-001", "title": "P&L Bronze ingestion", "task_type": "story",
         "from_status": "review", "hours_in_status": 8},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "from_status": "todo", "hours_in_status": 2},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "from_status": "in_progress", "hours_in_status": 24},
        {"task_id": "t-007", "title": "Balance Sheet DLT", "task_type": "story",
         "from_status": "review", "hours_in_status": 6},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "from_status": "todo", "hours_in_status": 1},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "from_status": "in_progress", "hours_in_status": 16},
        {"task_id": "t-008", "title": "Access policy — Finance", "task_type": "task",
         "from_status": "review", "hours_in_status": 4},
    ])


def get_retro_items() -> pd.DataFrame:
    return pd.DataFrame([
        {"retro_id": "ret-001", "sprint_id": "sp-003", "category": "went_well",
         "item_text": "DLT pipeline setup was smooth — reusable template pays off", "votes": 5},
        {"retro_id": "ret-002", "sprint_id": "sp-003", "category": "went_well",
         "item_text": "Good collaboration between data eng and finance BA", "votes": 3},
        {"retro_id": "ret-003", "sprint_id": "sp-003", "category": "improve",
         "item_text": "UAT environment setup took 2 days — need automation", "votes": 4},
        {"retro_id": "ret-004", "sprint_id": "sp-003", "category": "improve",
         "item_text": "Story points for infra tasks are consistently underestimated", "votes": 3},
        {"retro_id": "ret-005", "sprint_id": "sp-003", "category": "action",
         "item_text": "Create Terraform module for UAT workspace provisioning", "votes": 4},
        {"retro_id": "ret-006", "sprint_id": "sp-003", "category": "action",
         "item_text": "Add spike tasks for infra estimation research", "votes": 2},
    ])


def get_empty() -> pd.DataFrame:
    return pd.DataFrame()
