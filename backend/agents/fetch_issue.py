from tools.github_client import get_issue
from tools.sarvam_client import call_sarvam
from state import AgentState
from urllib.parse import urlparse

def parse_issue_url(issue_url: str):
    # Parses:
    # https://github.com/owner/repo/issues/42
    parts = urlparse(issue_url).path.strip("/").split("/")
    repo_name = f"{parts[0]}/{parts[1]}"
    issue_number = int(parts[3])
    return repo_name, issue_number

def fetch_issue_agent(state: AgentState) -> AgentState:
    print("🔍 FetchIssue Agent running...")

    # Step 1 — Parse URL
    repo_name, issue_number = parse_issue_url(
        state["issue_url"]
    )

    # Step 2 — Fetch from GitHub
    issue = get_issue(repo_name, issue_number)

    # Step 3 — Extract comments
    comments = [
        comment.body
        for comment in issue.get_comments()
    ]

    # Step 4 — Extract labels
    labels = [label.name for label in issue.labels]

    # Step 5 — Use Sarvam to summarize issue
    summary_prompt = f"""
    Summarize this GitHub issue clearly:
    
    Title: {issue.title}
    Description: {issue.body}
    Comments: {comments}
    
    Give a short 2-3 line summary of what 
    needs to be fixed.
    """

    summary = call_sarvam(summary_prompt)
    print(f"✅ Issue fetched: {issue.title}")
    print(f"📝 Summary: {summary}")

    # Step 6 — Update state
    return {
        **state,
        "issue_title": issue.title,
        "issue_body": issue.body,
        "issue_labels": labels,
        "issue_comments": comments,
        "repo_name": repo_name,
        "issue_number": issue_number
    }