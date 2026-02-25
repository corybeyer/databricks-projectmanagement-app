"""
Data Access Layer — Unity Catalog Queries
==========================================
All database interactions go through this module.
Uses Databricks SDK for serverless SQL warehouse queries.
Falls back to sample data when running locally for development.
"""

import os
import json
from datetime import datetime, date, timedelta
from typing import Optional
import pandas as pd

# ─── Databricks Connection ──────────────────────────────────
CATALOG = "workspace"
SCHEMA = "project_management"

def _get_sql_connection():
    """Get Databricks SQL connection via SDK. Returns None if running locally."""
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.sql import StatementState
        w = WorkspaceClient()
        return w
    except Exception:
        return None

def query(sql: str, params: dict = None) -> pd.DataFrame:
    """
    Execute SQL against Unity Catalog and return DataFrame.
    Falls back to sample data when Databricks SDK unavailable.
    """
    client = _get_sql_connection()
    if client is None:
        # Running locally — return sample data
        return _sample_data_fallback(sql)
    
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    try:
        result = client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            catalog=CATALOG,
            schema=SCHEMA,
        )
        if result.result and result.result.data_array:
            columns = [col.name for col in result.manifest.schema.columns]
            return pd.DataFrame(result.result.data_array, columns=columns)
        return pd.DataFrame()
    except Exception as e:
        print(f"Query error: {e}")
        return pd.DataFrame()


# ─── Domain Queries ─────────────────────────────────────────

def get_portfolios() -> pd.DataFrame:
    return query("""
        SELECT p.*,
               COUNT(DISTINCT pr.project_id) as project_count,
               AVG(pr.pct_complete) as avg_completion,
               SUM(pr.budget_spent) as total_spent,
               SUM(pr.budget_total) as total_budget
        FROM portfolios p
        LEFT JOIN projects pr ON p.portfolio_id = pr.portfolio_id
        GROUP BY ALL
        ORDER BY p.name
    """)

def get_portfolio_projects(portfolio_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT pr.*,
               ph.name as current_phase_name,
               ph.phase_type,
               s.name as active_sprint_name,
               s.sprint_id as active_sprint_id
        FROM projects pr
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        LEFT JOIN sprints s ON pr.project_id = s.project_id AND s.status = 'active'
        WHERE pr.portfolio_id = '{portfolio_id}'
        ORDER BY pr.priority_rank
    """)

def get_project_detail(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT pr.*,
               pf.name as portfolio_name,
               ph.name as current_phase_name,
               ph.delivery_method
        FROM projects pr
        LEFT JOIN portfolios pf ON pr.portfolio_id = pf.portfolio_id
        LEFT JOIN phases ph ON pr.current_phase_id = ph.phase_id
        WHERE pr.project_id = '{project_id}'
    """)

def get_project_charter(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT c.*
        FROM project_charters c
        WHERE c.project_id = '{project_id}'
    """)

def get_project_phases(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT ph.*,
               COUNT(DISTINCT t.task_id) as task_count,
               COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.task_id END) as done_count
        FROM phases ph
        LEFT JOIN tasks t ON ph.phase_id = t.phase_id
        WHERE ph.project_id = '{project_id}'
        GROUP BY ALL
        ORDER BY ph.phase_order
    """)

def get_sprints(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT s.*,
               SUM(t.story_points) as total_points,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as done_points
        FROM sprints s
        LEFT JOIN tasks t ON s.sprint_id = t.sprint_id
        WHERE s.project_id = '{project_id}'
        GROUP BY ALL
        ORDER BY s.start_date
    """)

def get_sprint_tasks(sprint_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT t.*,
               tm.display_name as assignee_name
        FROM tasks t
        LEFT JOIN team_members tm ON t.assignee = tm.user_id
        WHERE t.sprint_id = '{sprint_id}'
        ORDER BY t.backlog_rank
    """)

def get_backlog(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT t.*,
               tm.display_name as assignee_name
        FROM tasks t
        LEFT JOIN team_members tm ON t.assignee = tm.user_id
        WHERE t.project_id = '{project_id}'
          AND t.sprint_id IS NULL
        ORDER BY t.backlog_rank
    """)

def get_resource_allocations() -> pd.DataFrame:
    return query("""
        SELECT tm.user_id, tm.display_name, tm.role,
               pr.name as project_name,
               pr.project_id,
               COUNT(DISTINCT t.task_id) as task_count,
               SUM(t.story_points) as points_assigned,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as points_done
        FROM team_members tm
        LEFT JOIN tasks t ON tm.user_id = t.assignee AND t.status != 'done'
        LEFT JOIN projects pr ON t.project_id = pr.project_id
        WHERE tm.is_active = true
        GROUP BY ALL
        ORDER BY tm.display_name, pr.name
    """)

def get_risks(portfolio_id: str = None) -> pd.DataFrame:
    where = f"WHERE r.portfolio_id = '{portfolio_id}'" if portfolio_id else ""
    return query(f"""
        SELECT r.*,
               pr.name as project_name,
               pf.name as portfolio_name
        FROM risks r
        LEFT JOIN projects pr ON r.project_id = pr.project_id
        LEFT JOIN portfolios pf ON r.portfolio_id = pf.portfolio_id
        {where}
        ORDER BY r.risk_score DESC
    """)

def get_retro_items(sprint_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT ri.*
        FROM retro_items ri
        WHERE ri.sprint_id = '{sprint_id}'
        ORDER BY ri.votes DESC
    """)

def get_velocity(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT s.name as sprint_name,
               s.start_date,
               s.end_date,
               SUM(CASE WHEN t.status = 'done' THEN t.story_points ELSE 0 END) as completed_points,
               SUM(t.story_points) as committed_points,
               s.capacity_points
        FROM sprints s
        LEFT JOIN tasks t ON s.sprint_id = t.sprint_id
        WHERE s.project_id = '{project_id}'
          AND s.status = 'closed'
        GROUP BY ALL
        ORDER BY s.start_date
    """)

def get_burndown(sprint_id: str) -> pd.DataFrame:
    """Uses Delta time travel to reconstruct daily burndown."""
    return query(f"""
        WITH sprint_info AS (
            SELECT start_date, end_date
            FROM sprints WHERE sprint_id = '{sprint_id}'
        ),
        date_series AS (
            SELECT explode(sequence(
                (SELECT start_date FROM sprint_info),
                (SELECT end_date FROM sprint_info),
                interval 1 day
            )) as burn_date
        )
        SELECT d.burn_date,
               SUM(CASE WHEN t.status != 'done' THEN t.story_points ELSE 0 END) as remaining_points,
               SUM(t.story_points) as total_points
        FROM date_series d
        CROSS JOIN tasks t TIMESTAMP AS OF d.burn_date
        WHERE t.sprint_id = '{sprint_id}'
        GROUP BY d.burn_date
        ORDER BY d.burn_date
    """)

def get_status_cycle_times(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT t.task_id, t.title, t.task_type,
               st.from_status, st.to_status,
               st.transitioned_at,
               LEAD(st.transitioned_at) OVER (
                   PARTITION BY t.task_id ORDER BY st.transitioned_at
               ) as next_transition,
               TIMESTAMPDIFF(HOUR,
                   st.transitioned_at,
                   LEAD(st.transitioned_at) OVER (
                       PARTITION BY t.task_id ORDER BY st.transitioned_at
                   )
               ) as hours_in_status
        FROM status_transitions st
        JOIN tasks t ON st.task_id = t.task_id
        WHERE t.project_id = '{project_id}'
        ORDER BY t.task_id, st.transitioned_at
    """)

def get_gate_status(project_id: str) -> pd.DataFrame:
    return query(f"""
        SELECT g.*,
               ph.name as phase_name
        FROM gates g
        JOIN phases ph ON g.phase_id = ph.phase_id
        WHERE ph.project_id = '{project_id}'
        ORDER BY g.gate_order
    """)


# ─── Write Operations (CRUD) ───────────────────────────────

def create_task(task_data: dict) -> bool:
    """Insert a new task into Unity Catalog."""
    cols = ", ".join(task_data.keys())
    vals = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in task_data.values()])
    try:
        query(f"INSERT INTO tasks ({cols}) VALUES ({vals})")
        return True
    except Exception as e:
        print(f"Create task error: {e}")
        return False

def update_task_status(task_id: str, new_status: str, changed_by: str) -> bool:
    """Update task status and log transition."""
    try:
        # Get current status
        current = query(f"SELECT status FROM tasks WHERE task_id = '{task_id}'")
        old_status = current.iloc[0]["status"] if len(current) > 0 else "unknown"
        
        # Update task
        query(f"""
            UPDATE tasks 
            SET status = '{new_status}', updated_at = current_timestamp()
            WHERE task_id = '{task_id}'
        """)
        
        # Log transition
        query(f"""
            INSERT INTO status_transitions 
            (transition_id, task_id, from_status, to_status, changed_by, transitioned_at)
            VALUES (uuid(), '{task_id}', '{old_status}', '{new_status}', '{changed_by}', current_timestamp())
        """)
        return True
    except Exception as e:
        print(f"Update task error: {e}")
        return False

def move_task_to_sprint(task_id: str, sprint_id: str) -> bool:
    try:
        query(f"UPDATE tasks SET sprint_id = '{sprint_id}' WHERE task_id = '{task_id}'")
        return True
    except Exception as e:
        print(f"Move task error: {e}")
        return False


# ─── Sample Data Fallback (Local Development) ──────────────

def _sample_data_fallback(sql: str) -> pd.DataFrame:
    """Return realistic sample data when not connected to Databricks."""
    sql_lower = sql.lower().strip()
    
    if "from portfolios" in sql_lower:
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
    
    if "from projects" in sql_lower and "portfolio_id" in sql_lower:
        return pd.DataFrame([
            {"project_id": "prj-001", "name": "Unity Catalog Migration", "status": "active",
             "delivery_method": "hybrid", "pct_complete": 55, "current_phase_name": "Build",
             "health": "yellow", "budget_total": 420000, "budget_spent": 302400,
             "active_sprint_name": "Sprint 4", "start_date": "2026-01-06", "target_date": "2026-08-01"},
            {"project_id": "prj-002", "name": "DLT Pipeline Framework", "status": "active",
             "delivery_method": "agile", "pct_complete": 72, "current_phase_name": "Build",
             "health": "green", "budget_total": 320000, "budget_spent": 230400,
             "active_sprint_name": "Sprint 6", "start_date": "2026-01-13", "target_date": "2026-06-15"},
            {"project_id": "prj-003", "name": "Secrets Management Rollout", "status": "active",
             "delivery_method": "waterfall", "pct_complete": 85, "current_phase_name": "UAT",
             "health": "green", "budget_total": 80000, "budget_spent": 68000,
             "active_sprint_name": None, "start_date": "2025-11-01", "target_date": "2026-03-15"},
        ])
    
    if "from project_charters" in sql_lower:
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
    
    if "from sprints" in sql_lower:
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
    
    if "from tasks" in sql_lower:
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
    
    # Default empty
    return pd.DataFrame()
