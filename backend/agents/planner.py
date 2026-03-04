from tools.sarvam_client import call_sarvam
from state import AgentState
import json

def find_root_cause(
    issue_title: str,
    issue_body: str,
    file_contents: dict[str, str]
) -> str:

    # Prepare file summaries
    files_summary = ""
    for path, content in file_contents.items():
        # Only send first 1000 chars per file
        files_summary += f"\n\nFile: {path}\n{content[:1000]}"

    prompt = f"""
    You are a senior software engineer.
    
    Analyze this GitHub issue and the relevant code files.
    Identify the root cause of the problem.
    
    Issue Title: {issue_title}
    Issue Body: {issue_body}
    
    Relevant Code Files:
    {files_summary}
    
    Explain the root cause in 2-3 sentences.
    Be specific and technical.
    """

    response = call_sarvam(prompt)
    return response.strip()


def identify_files_to_edit(
    issue_title: str,
    root_cause: str,
    relevant_files: list[str]
) -> list[str]:

    files_list = "\n".join(relevant_files)

    prompt = f"""
    You are a senior software engineer.
    
    Given this GitHub issue and root cause,
    which files need to be edited to fix it?
    
    Issue Title: {issue_title}
    Root Cause: {root_cause}
    
    Available Files:
    {files_list}
    
    Return ONLY a JSON array of file paths that need editing:
    ["path/to/file1.py", "path/to/file2.py"]
    
    No explanation. Just the JSON array.
    Maximum 3 files.
    """

    response = call_sarvam(prompt)

    # Clean response
    response = response.strip()
    if "```" in response:
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]

    try:
        files = json.loads(response)
        return files[:3]
    except:
        return relevant_files[:1]


def create_fix_plan(
    issue_title: str,
    issue_body: str,
    root_cause: str,
    files_to_edit: list[str],
    file_contents: dict[str, str]
) -> str:

    # Get contents of files to edit
    edit_contents = ""
    for path in files_to_edit:
        if path in file_contents:
            edit_contents += f"\n\nFile: {path}\n{file_contents[path][:1000]}"

    prompt = f"""
    You are a senior software engineer.
    
    Create a clear step by step plan to fix this issue.
    
    Issue Title: {issue_title}
    Issue Body: {issue_body}
    Root Cause: {root_cause}
    
    Files to edit:
    {edit_contents}
    
    Write a numbered step by step fix plan.
    Be specific about what to change in each file.
    Keep it under 10 steps.
    """

    response = call_sarvam(prompt)
    return response.strip()


def planner_agent(state: AgentState) -> AgentState:
    print("\n🧠 Planner Agent running...")

    # Step 1 — Find root cause
    print("🔍 Finding root cause...")
    root_cause = find_root_cause(
        state["issue_title"],
        state["issue_body"],
        state["file_contents"]
    )
    print(f"✅ Root cause: {root_cause}")

    # Step 2 — Identify files to edit
    print("📝 Identifying files to edit...")
    files_to_edit = identify_files_to_edit(
        state["issue_title"],
        root_cause,
        state["relevant_files"]
    )
    print(f"✅ Files to edit: {files_to_edit}")

    # Step 3 — Create fix plan
    print("📋 Creating fix plan...")
    fix_approach = create_fix_plan(
        state["issue_title"],
        state["issue_body"],
        root_cause,
        files_to_edit,
        state["file_contents"]
    )
    print(f"✅ Fix plan created")
    print(f"\n{fix_approach}\n")

    return {
        **state,
        "root_cause": root_cause,
        "files_to_edit": files_to_edit,
        "fix_approach": fix_approach
    }