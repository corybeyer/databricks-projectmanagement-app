"""
Task & Sprint Field Definitions
================================
Shared CRUD modal field definitions for tasks and sprints.
Used by sprint.py, backlog.py, and my_work.py pages.
"""

TEAM_MEMBER_OPTIONS = [
    {"label": "Cory S.", "value": "u-001"},
    {"label": "Chris J.", "value": "u-002"},
    {"label": "Anna K.", "value": "u-003"},
]

TASK_FIELDS = [
    {"id": "title", "label": "Title", "type": "text", "required": True,
     "placeholder": "Task title"},
    {"id": "task_type", "label": "Type", "type": "select", "required": True,
     "options": [
         {"label": "Epic", "value": "epic"},
         {"label": "Story", "value": "story"},
         {"label": "Task", "value": "task"},
         {"label": "Bug", "value": "bug"},
         {"label": "Subtask", "value": "subtask"},
     ]},
    {"id": "priority", "label": "Priority", "type": "select", "required": True,
     "options": [
         {"label": "Critical", "value": "critical"},
         {"label": "High", "value": "high"},
         {"label": "Medium", "value": "medium"},
         {"label": "Low", "value": "low"},
     ]},
    {"id": "story_points", "label": "Story Points", "type": "number",
     "required": False, "min": 0, "max": 100, "placeholder": "0"},
    {"id": "assignee", "label": "Assignee", "type": "select", "required": False,
     "options": TEAM_MEMBER_OPTIONS, "placeholder": "Unassigned"},
    {"id": "description", "label": "Description", "type": "textarea",
     "required": False, "rows": 3, "placeholder": "Task description..."},
]

SPRINT_FIELDS = [
    {"id": "name", "label": "Sprint Name", "type": "text", "required": True,
     "placeholder": "Sprint 5"},
    {"id": "goal", "label": "Sprint Goal", "type": "textarea", "required": False,
     "rows": 2, "placeholder": "What is the goal of this sprint?"},
    {"id": "start_date", "label": "Start Date", "type": "date", "required": True},
    {"id": "end_date", "label": "End Date", "type": "date", "required": True},
    {"id": "capacity_points", "label": "Capacity (Points)", "type": "number",
     "required": False, "min": 0, "max": 999, "placeholder": "0"},
]
