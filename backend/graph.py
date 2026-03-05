from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agents.fetch_issue import fetch_issue_agent
from agents.research import research_agent
from agents.validator import validator_agent
from agents.planner import planner_agent
from agents.fix import fix_agent
from agents.test_runner import test_runner_agent
from agents.pr_creator import pr_creator_agent
from state import AgentState

MAX_RETRIES = 3

def should_proceed_or_stop(state: AgentState) -> str:
    if not state["should_proceed"]:
        print(f"🛑 Stopping: {state['skip_reason']}")
        return "stop"
    return "continue"

def should_retry_or_wait(state: AgentState) -> str:
    if state["test_passed"]:
        print("✅ Tests passed → Waiting for approval")
        return "wait_for_approval"
    if state["retry_count"] >= MAX_RETRIES:
        print("❌ Max retries reached → Stopping")
        return "end"
    print(f"🔄 Tests failed → Retrying fix")
    return "retry_fix"


def build_graph():
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("fetch_issue", fetch_issue_agent)
    workflow.add_node("research", research_agent)
    workflow.add_node("validator", validator_agent)
    workflow.add_node("planner", planner_agent)
    workflow.add_node("fix", fix_agent)
    workflow.add_node("test", test_runner_agent)
    workflow.add_node("create_pr", pr_creator_agent)

    # Edges
    workflow.add_edge("fetch_issue", "research")
    workflow.add_edge("research", "validator")

    # After validator — proceed or stop
    workflow.add_conditional_edges(
        "validator",
        should_proceed_or_stop,
        {
            "continue": "planner",
            "stop": END
        }
    )

    workflow.add_edge("planner", "fix")
    workflow.add_edge("fix", "test")

    # After test — retry or wait for approval
    workflow.add_conditional_edges(
        "test",
        should_retry_or_wait,
        {
            "wait_for_approval": "create_pr",
            "retry_fix": "fix",
            "end": END
        }
    )

    workflow.add_edge("create_pr", END)
    workflow.set_entry_point("fetch_issue")

    memory = MemorySaver()

    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["create_pr"]
    )

graph = build_graph()
