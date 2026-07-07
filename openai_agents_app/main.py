from __future__ import annotations

import asyncio
from typing import Literal

from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

from shared.task_tools import (
    add_task as store_add_task,
    clear_all_tasks as store_clear_all_tasks,
    get_today_plan as store_get_today_plan,
    list_tasks as store_list_tasks,
    mark_task_done as store_mark_task_done,
    update_task as store_update_task,
)

load_dotenv()

Priority = Literal["low", "medium", "high"]
StatusFilter = Literal["pending", "done", "all"]


@function_tool
def add_task(
    title: str, due_date: str | None = None, priority: Priority = "medium"
) -> str:
    """Add a new task to the task manager."""
    return store_add_task(title=title, due_date=due_date, priority=priority)


@function_tool
def list_tasks(status: StatusFilter = "pending") -> str:
    """List tasks. Use status='all' when the user wants everything."""
    return store_list_tasks(status=status)


@function_tool
def mark_task_done(task_id: int) -> str:
    """Mark a task as done."""
    return store_mark_task_done(task_id=task_id)


@function_tool
def update_task(task_id: int, field: str, value: str) -> str:
    """Update a task field. Allowed fields: title, due_date, priority, status."""
    return store_update_task(task_id=task_id, field=field, value=value)


@function_tool
def get_today_plan() -> str:
    """Get a priority-ordered plan for today's pending tasks."""
    return store_get_today_plan()


@function_tool
def clear_all_tasks() -> str:
    """Clear all tasks. Only use this when the user explicitly asks to reset the demo."""
    return store_clear_all_tasks()


task_agent = Agent(
    name="Task Manager Agent",
    model="gpt-4.1-mini",
    instructions="""
You are a practical task manager agent.

Rules:
- Use tools whenever the user asks to add, list, update, complete, clear, or plan tasks.
- Ask a follow-up question if the user wants to add a task but the title is missing.
- Do not invent task ids. List tasks first if the user refers to a task vaguely.
- Keep final answers concise and show important task ids.
- For 'plan my day', call get_today_plan and summarize the order clearly.
""".strip(),
    tools=[
        add_task,
        list_tasks,
        mark_task_done,
        update_task,
        get_today_plan,
        clear_all_tasks,
    ],
)


async def main() -> None:
    print("OpenAI Agents SDK Task Manager")
    print("Try: add a high priority task to record the LangGraph section tomorrow")
    print("Type 'exit' to quit.\n")

    conversation_history = []

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Agent: Bye!")
            break

        if not user_input:
            continue

        agent_input = conversation_history + [
            {
                "role": "user",
                "content": user_input,
            }
        ]

        result = await Runner.run(task_agent, agent_input)
        print(f"Agent: {result.final_output}\n")
        conversation_history = result.to_input_list()


if __name__ == "__main__":
    asyncio.run(main())
