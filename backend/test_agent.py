from agents.fetch_issue import fetch_issue_agent
from agents.research import research_agent
from agents.planner import planner_agent
from agents.fix import fix_agent
from agents.test_runner import test_runner_agent
from agents.pr_creator import pr_creator_agent

state = {
    "issue_url": "https://github.com/vikask011/test-agent-repo/issues/1",
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
print(f"Files to edit: {state['files_to_edit']}")

# Agent 4
state = fix_agent(state)
print(f"\n✅ Agent 4 done")
print(f"Fixed files: {list(state['proposed_fix'].keys())}")

# Agent 5
state = test_runner_agent(state)
print(f"\n✅ Agent 5 done")
print(f"Tests passed: {state['test_passed']}")

# Agent 6
state = pr_creator_agent(state)
print(f"\n✅ Agent 6 done")
print(f"PR URL: {state['pr_url']}")