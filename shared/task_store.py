from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Priority = Literal["low", "medium", "high"]
Status = Literal["pending", "done"]


def _data_path() -> Path:
    configured = os.getenv("TASKS_DB_PATH")
    if configured:
        return Path(configured).expanduser().resolve()
    # repo_root/tasks.json
    return Path(__file__).resolve().parents[1] / "tasks.json"


@dataclass
class Task:
    id: int
    title: str
    due_date: str | None = None
    priority: Priority = "medium"
    status: Status = "pending"
    created_at: str = ""
    completed_at: str | None = None


class TaskStore:
    """A tiny JSON task store used by all 3 framework examples."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or _data_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"next_id": 1, "tasks": []})

    def _read(self) -> dict[str, Any]:
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_task(
        self,
        title: str,
        due_date: str | None = None,
        priority: Priority = "medium",
    ) -> dict[str, Any]:
        title = title.strip()
        if not title:
            raise ValueError("title cannot be empty")
        if priority not in {"low", "medium", "high"}:
            raise ValueError("priority must be low, medium, or high")

        data = self._read()
        task = Task(
            id=int(data["next_id"]),
            title=title,
            due_date=due_date,
            priority=priority,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        data["next_id"] = int(data["next_id"]) + 1
        data["tasks"].append(asdict(task))
        self._write(data)
        return asdict(task)

    def list_tasks(
        self, status: Status | Literal["all"] = "pending"
    ) -> list[dict[str, Any]]:
        data = self._read()
        tasks: list[dict[str, Any]] = data["tasks"]
        if status == "all":
            return tasks
        return [task for task in tasks if task["status"] == status]

    def mark_task_done(self, task_id: int) -> dict[str, Any]:
        data = self._read()
        for task in data["tasks"]:
            if int(task["id"]) == int(task_id):
                task["status"] = "done"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                self._write(data)
                return task
        raise ValueError(f"No task found with id={task_id}")

    def update_task(self, task_id: int, field: str, value: str) -> dict[str, Any]:
        allowed_fields = {"title", "due_date", "priority", "status"}
        if field not in allowed_fields:
            raise ValueError(
                f"field must be one of: {', '.join(sorted(allowed_fields))}"
            )
        if field == "priority" and value not in {"low", "medium", "high"}:
            raise ValueError("priority must be low, medium, or high")
        if field == "status" and value not in {"pending", "done"}:
            raise ValueError("status must be pending or done")

        data = self._read()
        for task in data["tasks"]:
            if int(task["id"]) == int(task_id):
                task[field] = value
                if field == "status" and value == "done":
                    task["completed_at"] = datetime.now(timezone.utc).isoformat()
                self._write(data)
                return task
        raise ValueError(f"No task found with id={task_id}")

    def clear_all(self) -> dict[str, Any]:
        self._write({"next_id": 1, "tasks": []})
        return {"ok": True, "message": "All tasks cleared"}
