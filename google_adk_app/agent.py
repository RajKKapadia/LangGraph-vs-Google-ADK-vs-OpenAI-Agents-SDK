from __future__ import annotations

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from shared.task_tools import (
    add_task,
    clear_all_tasks,
    get_today_plan,
    list_tasks,
    mark_task_done,
    update_task,
)

# ADK discovers this variable when you run:
#   adk run google_adk_app
# or:
#   adk web .
root_agent = Agent(
    name="task_manager_agent",
    model="gemini-2.5-flash",
    description="A practical task manager agent that can add, list, update, complete, and plan tasks.",
    instruction="""
You are a practical task manager agent.

Rules:
- Use tools whenever the user asks to add, list, update, complete, clear, or plan tasks.
- Ask a follow-up question if the user wants to add a task but the title is missing.
- Do not invent task ids. List tasks first if the user refers to a task vaguely.
- Keep final answers concise and show important task ids.
- For 'plan my day', call get_today_plan and summarize the order clearly.
""".strip(),
    tools=[
        FunctionTool(add_task),
        FunctionTool(list_tasks),
        FunctionTool(mark_task_done),
        FunctionTool(update_task),
        FunctionTool(get_today_plan),
        FunctionTool(clear_all_tasks),
    ],
)
