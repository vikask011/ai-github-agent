from fastapi import FastAPI
from pydantic import BaseModel
from agents.fetch_issue import fetch_issue_agent
from agents.research import research_agent
from agents.planner import planner_agent
from agents.fix import fix_agent
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
        "diff": {}
    }

@app.get("/")
def root():
    return {"status": "AI GitHub Agent is running"}

@app.post("/fetch-issue")
def fetch_issue(request: IssueRequest):
    state = get_initial_state(request.issue_url)
    state = fetch_issue_agent(state)
    return {
        "status": "success",
        "data": {
            "title": state["issue_title"],
            "repo_name": state["repo_name"],
            "labels": state["issue_labels"]
        }
    }

@app.post("/research")
def research(request: IssueRequest):
    state = get_initial_state(request.issue_url)
    state = fetch_issue_agent(state)
    state = research_agent(state)
    return {
        "status": "success",
        "data": {
            "keywords": state["keywords"],
            "relevant_files": state["relevant_files"]
        }
    }

@app.post("/plan")
def plan(request: IssueRequest):
    state = get_initial_state(request.issue_url)
    state = fetch_issue_agent(state)
    state = research_agent(state)
    state = planner_agent(state)
    return {
        "status": "success",
        "data": {
            "root_cause": state["root_cause"],
            "files_to_edit": state["files_to_edit"],
            "fix_approach": state["fix_approach"]
        }
    }

@app.post("/fix")
def fix(request: IssueRequest):
    state = get_initial_state(request.issue_url)
    state = fetch_issue_agent(state)
    state = research_agent(state)
    state = planner_agent(state)
    state = fix_agent(state)
    return {
        "status": "success",
        "data": {
            "fixed_files": list(state["proposed_fix"].keys()),
            "diffs": {
                path: diff[:1000]
                for path, diff
                in state["diff"].items()
            }
        }
    }