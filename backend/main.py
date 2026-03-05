from fastapi import FastAPI
from pydantic import BaseModel
from graph import graph
from state import AgentState
from dotenv import load_dotenv
import uuid

load_dotenv()

app = FastAPI(title="AI GitHub Agent")

class IssueRequest(BaseModel):
    issue_url: str

class ApproveRequest(BaseModel):
    thread_id: str

def get_initial_state(issue_url: str) -> AgentState:
    return {
        "issue_url": issue_url,
        "issue_title": "",
        "issue_body": "",
        "issue_labels": [],
        "issue_comments": [],
        "repo_name": "",
        "issue_number": 0,
        "keywords": [],
        "relevant_files": [],
        "file_contents": {},
        "root_cause": "",
        "files_to_edit": [],
        "fix_approach": "",
        "proposed_fix": {},
        "diff": {},
        "should_proceed": True,
        "skip_reason": "",
        "test_passed": False,
        "test_output": "",
        "retry_count": 0,
        "pr_url": "",
        "branch_name": ""
    }

@app.get("/")
def root():
    return {"status": "AI GitHub Agent is running"}

@app.post("/solve")
def solve(request: IssueRequest):
    """
    Runs Agent 1 → 2 → Validator → 3 → 4 → 5
    Pauses before Agent 6.
    Returns results + thread_id for approval.
    """
    print(f"\n📥 Received: {request.issue_url}")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    state = get_initial_state(request.issue_url)
    result = graph.invoke(state, config)

    # Case 1 — Validator stopped the graph
    if not result.get("should_proceed", True):
        return {
            "status": "already_fixed",
            "message": result["skip_reason"],
            "data": {
                "title": result["issue_title"],
                "reason": result["skip_reason"]
            }
        }

    # Case 2 — Tests failed and max retries reached
    if not result["test_passed"]:
        return {
            "status": "fix_failed",
            "message": "Could not fix the issue after max retries",
            "data": {
                "title": result["issue_title"],
                "test_output": result["test_output"]
            }
        }

    # Case 3 — Tests passed, waiting for approval
    return {
        "status": "awaiting_approval",
        "thread_id": thread_id,
        "data": {
            "title": result["issue_title"],
            "root_cause": result["root_cause"],
            "files_fixed": list(result["proposed_fix"].keys()),
            "tests_passed": result["test_passed"],
            "test_output": result["test_output"],
            "diff": {
                path: diff[:500]
                for path, diff
                in result["diff"].items()
            }
        }
    }

@app.post("/approve-pr")
def approve_pr(request: ApproveRequest):
    """
    User clicked 'Create Pull Request'.
    Resumes graph from paused state.
    Agent 6 runs and creates PR.
    """
    print(f"\n✅ User approved PR: {request.thread_id}")

    config = {"configurable": {"thread_id": request.thread_id}}

    result = graph.invoke(None, config)

    if not result.get("pr_url"):
        return {
            "status": "error",
            "message": "PR creation failed"
        }

    return {
        "status": "success",
        "data": {
            "pr_url": result["pr_url"],
            "branch_name": result["branch_name"]
        }
    }

@app.post("/cancel-pr")
def cancel_pr(request: ApproveRequest):
    """
    User clicked 'Cancel'.
    No PR created.
    """
    print(f"\n❌ User cancelled PR: {request.thread_id}")
    return {
        "status": "cancelled",
        "message": "PR creation cancelled by user"
    }
