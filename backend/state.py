from typing import TypedDict

class AgentState(TypedDict):
    # Input
    issue_url: str

    # FetchIssue fills these
    issue_title: str
    issue_body: str
    issue_labels: list[str]
    issue_comments: list[str]
    repo_name: str
    issue_number: int

    # Research fills these
    keywords: list[str]
    relevant_files: list[str]
    file_contents: dict[str, str]

    # Planner fills these
    root_cause: str
    files_to_edit: list[str]
    fix_approach: str

    # Fix fills these
    proposed_fix: dict[str, str]
    diff: dict[str, str]

    # Test Runner fills these
    test_passed: bool
    test_output: str
    retry_count: int

    # PR Creator fills these
    pr_url: str
    branch_name: str