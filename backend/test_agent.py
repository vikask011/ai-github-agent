from agents.fetch_issue import fetch_issue_agent
from agents.research import research_agent
from agents.planner import planner_agent

state = {
    "issue_url": "https://github.com/facebook/react/issues/1",
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
    "fix_approach": ""
}

# Agent 1
state = fetch_issue_agent(state)
print(f"\n✅ Agent 1 done: {state['issue_title']}")

# Agent 2
state = research_agent(state)
print(f"\n✅ Agent 2 done")
print(f"Relevant files: {state['relevant_files']}")

# Agent 3
state = planner_agent(state)
print(f"\n✅ Agent 3 done")
print(f"Root cause: {state['root_cause']}")
print(f"Files to edit: {state['files_to_edit']}")
print(f"Fix approach:\n{state['fix_approach']}")