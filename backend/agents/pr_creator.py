from tools.github_client import get_repo
from tools.sarvam_client import call_sarvam
from state import AgentState
import base64

def generate_pr_description(
    issue_title: str,
    issue_number: int,
    root_cause: str,
    fix_approach: str,
    test_output: str
) -> str:

    prompt = f"""
    Write a clean Pull Request description.
    
    Issue: {issue_title}
    Root Cause: {root_cause}
    Fix Applied: {fix_approach[:500]}
    Test Results: All tests passed
    
    Include:
    - What the problem was
    - What was changed to fix it
    - That all tests pass
    
    Keep it under 200 words.
    Professional tone.
    """

    return call_sarvam(prompt)


def pr_creator_agent(state: AgentState) -> AgentState:
    print("\n🚀 PR Creator Agent running...")

    # Skip if tests failed
    if not state["test_passed"]:
        print("❌ Skipping PR — tests did not pass")
        return {
            **state,
            "pr_url": "",
            "branch_name": ""
        }

    repo = get_repo(state["repo_name"])
    issue_number = state["issue_number"]

    # Step 1 — Create branch name
    branch_name = f"fix/issue-{issue_number}-auto-fix"
    print(f"🌿 Creating branch: {branch_name}")

    # Step 2 — Get main branch SHA
    main_branch = repo.get_branch("main")
    main_sha = main_branch.commit.sha

    # Step 3 — Create new branch
    try:
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=main_sha
        )
        print(f"✅ Branch created: {branch_name}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️ Branch already exists. Using it.")
        else:
            print(f"❌ Branch error: {e}")
            return {**state, "pr_url": "", "branch_name": ""}

    # Step 4 — Commit each fixed file
    for file_path, fixed_content in state["proposed_fix"].items():
        try:
            # Get current file SHA
            current_file = repo.get_contents(
                file_path,
                ref=branch_name
            )

            # Update file on branch
            repo.update_file(
                path=file_path,
                message=f"fix: {file_path} — issue #{issue_number}",
                content=fixed_content,
                sha=current_file.sha,
                branch=branch_name
            )
            print(f"✅ Committed: {file_path}")

        except Exception as e:
            print(f"❌ Commit error for {file_path}: {e}")
            continue

    # Step 5 — Generate PR description
    print("📝 Generating PR description...")
    pr_body = generate_pr_description(
        issue_title=state["issue_title"],
        issue_number=issue_number,
        root_cause=state["root_cause"],
        fix_approach=state["fix_approach"],
        test_output=state["test_output"]
    )

    # Step 6 — Create Pull Request
    print("🔀 Creating Pull Request...")
    try:
        pr = repo.create_pull(
            title=f"Fix: {state['issue_title']} (#{issue_number})",
            body=pr_body,
            head=branch_name,
            base="main"
        )
        print(f"✅ PR created: {pr.html_url}")

        return {
            **state,
            "pr_url": pr.html_url,
            "branch_name": branch_name
        }

    except Exception as e:
        print(f"❌ PR creation error: {e}")
        return {
            **state,
            "pr_url": "",
            "branch_name": branch_name
        }