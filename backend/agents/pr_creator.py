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

    if not state["test_passed"]:
        print("❌ Skipping PR — tests did not pass")
        return {**state, "pr_url": "", "branch_name": ""}

    repo = get_repo(state["repo_name"])
    issue_number = state["issue_number"]

    # Auto-detect default branch (main or master)
    default_branch = repo.default_branch
    print(f"🌿 Default branch: {default_branch}")

    branch_name = f"fix/issue-{issue_number}-auto-fix"
    print(f"🌿 Creating branch: {branch_name}")

    # Get default branch SHA
    try:
        base_branch = repo.get_branch(default_branch)
        base_sha = base_branch.commit.sha
    except Exception as e:
        print(f"❌ Could not get base branch: {e}")
        return {**state, "pr_url": "", "branch_name": ""}

    # Create new branch
    try:
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_sha
        )
        print(f"✅ Branch created: {branch_name}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"⚠️ Branch already exists. Using it.")
        else:
            print(f"❌ Branch error: {e}")
            return {**state, "pr_url": "", "branch_name": ""}

    # Commit each fixed file
    for file_path, fixed_content in state["proposed_fix"].items():
        try:
            current_file = repo.get_contents(
                file_path,
                ref=branch_name
            )
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

    # Generate PR description
    print("📝 Generating PR description...")
    pr_body = generate_pr_description(
        issue_title=state["issue_title"],
        issue_number=issue_number,
        root_cause=state["root_cause"],
        fix_approach=state["fix_approach"],
        test_output=state["test_output"]
    )

    # Create Pull Request
    print("🔀 Creating Pull Request...")
    try:
        pr = repo.create_pull(
            title=f"Fix: {state['issue_title']} (#{issue_number})",
            body=pr_body,
            head=branch_name,
            base=default_branch  # use detected branch
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
