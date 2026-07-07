from __future__ import annotations

from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from shared.task_tools import (
    add_task,
    clear_all_tasks,
    get_today_plan,
    list_tasks,
    mark_task_done,
    update_task,
)

load_dotenv()

Action = Literal[
    "add_task",
    "list_tasks",
    "mark_task_done",
    "update_task",
    "get_today_plan",
    "clear_all_tasks",
    "respond",
]
Priority = Literal["low", "medium", "high"]
StatusFilter = Literal["pending", "done", "all"]


class ToolPlan(BaseModel):
    """The LLM's structured decision about what the graph should do next."""

    action: Action = Field(description="The tool/workflow action to run.")
    needs_clarification: bool = Field(default=False)
    clarification_question: str | None = Field(default=None)

    title: str | None = Field(default=None)
    due_date: str | None = Field(default=None)
    priority: Priority = Field(default="medium")
    status: StatusFilter = Field(default="pending")
    task_id: int | None = Field(default=None)
    field: str | None = Field(default=None)
    value: str | None = Field(default=None)
    response: str | None = Field(default=None)


class TaskState(TypedDict, total=False):
    user_input: str
    plan: ToolPlan
    tool_result: str
    final_response: str


planner_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0).with_structured_output(
    ToolPlan
)
writer_llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.2)


PLANNER_PROMPT = """
You are the planner node inside a LangGraph task manager.
Convert the user's message into exactly one action.

Available actions:
- add_task: requires title. due_date can be natural language. priority defaults to medium.
- list_tasks: status can be pending, done, or all.
- mark_task_done: requires task_id.
- update_task: requires task_id, field, and value.
- get_today_plan: use when the user asks what to focus on or how to plan their day.
- clear_all_tasks: only when the user explicitly asks to reset/clear the demo.
- respond: use for normal conversation unrelated to tasks.

Clarification rules:
- If adding a task and no title is present, set needs_clarification=true.
- If completing/updating a task and the id is missing, set needs_clarification=true and ask the user to provide/list task id.
- Do not invent ids.
""".strip()


def plan_node(state: TaskState) -> TaskState:
    plan = planner_llm.invoke(
        [
            ("system", PLANNER_PROMPT),
            ("user", state["user_input"]),
        ]
    )
    return {"plan": plan}


def route_after_plan(state: TaskState) -> str:
    plan = state["plan"]
    if plan.needs_clarification:
        return "clarify"
    if plan.action == "respond":
        return "respond"
    return "execute_tool"


def clarify_node(state: TaskState) -> TaskState:
    plan = state["plan"]
    question = (
        plan.clarification_question or "Can you provide the missing task details?"
    )
    return {"final_response": question}


def respond_node(state: TaskState) -> TaskState:
    plan = state["plan"]
    return {
        "final_response": plan.response
        or "I can help you add, list, update, complete, and plan tasks."
    }


def execute_tool_node(state: TaskState) -> TaskState:
    plan = state["plan"]

    if plan.action == "add_task":
        if not plan.title:
            return {"final_response": "What task should I add?"}
        result = add_task(
            title=plan.title, due_date=plan.due_date, priority=plan.priority
        )

    elif plan.action == "list_tasks":
        result = list_tasks(status=plan.status)

    elif plan.action == "mark_task_done":
        if plan.task_id is None:
            return {"final_response": "Which task id should I mark as done?"}
        result = mark_task_done(task_id=plan.task_id)

    elif plan.action == "update_task":
        if plan.task_id is None or not plan.field or plan.value is None:
            return {
                "final_response": "Please provide the task id, field, and new value."
            }
        result = update_task(task_id=plan.task_id, field=plan.field, value=plan.value)

    elif plan.action == "get_today_plan":
        result = get_today_plan()

    elif plan.action == "clear_all_tasks":
        result = clear_all_tasks()

    else:
        result = "No tool executed."

    return {"tool_result": result}


def summarize_node(state: TaskState) -> TaskState:
    response = writer_llm.invoke(
        [
            (
                "system",
                "You are a concise task manager assistant. Summarize the tool result for the user. Mention task ids when useful.",
            ),
            (
                "user",
                f"User request: {state['user_input']}\n\nTool result:\n{state.get('tool_result', '')}",
            ),
        ]
    )
    return {"final_response": response.content}


def build_graph():
    builder = StateGraph(TaskState)

    builder.add_node("plan", plan_node)
    builder.add_node("clarify", clarify_node)
    builder.add_node("respond", respond_node)
    builder.add_node("execute_tool", execute_tool_node)
    builder.add_node("summarize", summarize_node)

    builder.add_edge(START, "plan")
    builder.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "clarify": "clarify",
            "respond": "respond",
            "execute_tool": "execute_tool",
        },
    )
    builder.add_edge("execute_tool", "summarize")
    builder.add_edge("clarify", END)
    builder.add_edge("respond", END)
    builder.add_edge("summarize", END)

    return builder.compile()


def main() -> None:
    graph = build_graph()

    png_bytes = graph.get_graph().draw_mermaid_png()

    with open("graph.png", "wb") as f:
        f.write(png_bytes)

    print("LangGraph Task Manager")
    print("Try: add a high priority task to record the LangGraph section tomorrow")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break

        result = graph.invoke({"user_input": user_input})
        print(f"Agent: {result['final_response']}\n")


if __name__ == "__main__":
    main()
