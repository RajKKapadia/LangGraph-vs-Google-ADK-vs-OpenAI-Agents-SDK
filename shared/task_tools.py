from __future__ import annotations

import json
import os
from datetime import date
from typing import Literal

from .task_store import TaskStore

Priority = Literal["low", "medium", "high"]
StatusFilter = Literal["pending", "done", "all"]


def _log_tool(name: str, tool_input: dict, tool_output: object) -> None:
    if os.getenv("SHOW_TOOL_LOGS", "1") != "1":
        return
    print("\n" + "=" * 72)
    print(f"🔧 TOOL USED: {name}")
    print("INPUT:")
    print(json.dumps(tool_input, indent=2, ensure_ascii=False))
    print("OUTPUT:")
    print(json.dumps(tool_output, indent=2, ensure_ascii=False))
    print("=" * 72 + "\n")


def _to_json(data: object) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def add_task(
    title: str, due_date: str | None = None, priority: Priority = "medium"
) -> str:
    """Add a new task. due_date can be natural language like 'tomorrow morning' or an ISO date."""
    result = TaskStore().add_task(title=title, due_date=due_date, priority=priority)
    _log_tool(
        "add_task", {"title": title, "due_date": due_date, "priority": priority}, result
    )
    return _to_json(result)


def list_tasks(status: StatusFilter = "pending") -> str:
    """List tasks by status. Use status='all' to include completed tasks."""
    result = TaskStore().list_tasks(status=status)
    _log_tool("list_tasks", {"status": status}, result)
    return _to_json(result)


def mark_task_done(task_id: int) -> str:
    """Mark a task as done using its numeric task id."""
    result = TaskStore().mark_task_done(task_id=task_id)
    _log_tool("mark_task_done", {"task_id": task_id}, result)
    return _to_json(result)


def update_task(task_id: int, field: str, value: str) -> str:
    """Update one task field. Allowed fields: title, due_date, priority, status."""
    result = TaskStore().update_task(task_id=task_id, field=field, value=value)
    _log_tool(
        "update_task", {"task_id": task_id, "field": field, "value": value}, result
    )
    return _to_json(result)


def get_today_plan() -> str:
    """Return a focused plan using pending tasks. The model should summarize/prioritize this for the user."""
    tasks = TaskStore().list_tasks(status="pending")
    high = [t for t in tasks if t["priority"] == "high"]
    medium = [t for t in tasks if t["priority"] == "medium"]
    low = [t for t in tasks if t["priority"] == "low"]
    result = {
        "date": date.today().isoformat(),
        "pending_count": len(tasks),
        "suggested_order": high + medium + low,
    }
    _log_tool("get_today_plan", {}, result)
    return _to_json(result)


def clear_all_tasks() -> str:
    """Clear all tasks. Useful while recording demos."""
    result = TaskStore().clear_all()
    _log_tool("clear_all_tasks", {}, result)
    return _to_json(result)
