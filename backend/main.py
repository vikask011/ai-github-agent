from fastapi import FastAPI
from pydantic import BaseModel
from agents.fetch_issue import fetch_issue_agent
from agents.research import research_agent
from agents.planner import planner_agent
from agents.fix import fix_agent
from agents.test_runner import test_runner_agent
from agents.pr_creator import pr_creator_agent
from state import AgentState
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI GitHub Agent")

class IssueRequest(BaseModel):
    issue_url: str

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
    state = get_initial_state(request.issue_url)

    state = fetch_issue_agent(state)
    state = research_agent(state)
    state = planner_agent(state)
    state = fix_agent(state)
    state = test_runner_agent(state)
    state = pr_creator_agent(state)

    return {
        "status": "success",
        "data": {
            "title": state["issue_title"],
            "root_cause": state["root_cause"],
            "files_fixed": list(state["proposed_fix"].keys()),
            "tests_passed": state["test_passed"],
            "pr_url": state["pr_url"]
        }
    }