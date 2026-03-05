from tools.sarvam_client import call_sarvam
from state import AgentState
import difflib

def generate_fix_for_file(
    file_path: str,
    current_code: str,
    fix_approach: str,
    root_cause: str,
    issue_title: str
) -> str:

    prompt = f"""
    You are a senior software engineer.
    Fix the bug in this file.
    
    Issue: {issue_title}
    Root Cause: {root_cause}
    
    Fix Plan:
    {fix_approach}
    
    Current code in {file_path}:
    {current_code}
    
    Rules:
    - Return the COMPLETE fixed file
    - Keep ALL existing imports exactly as they are
    - Keep ALL existing functions
    - Only change what is needed to fix the bug
    - Return ONLY raw code
    - No markdown, no explanation, no code blocks
    - No triple backticks
    - First line must be valid Python code
    """

    fixed_code = call_sarvam(prompt)

    # Clean response
    fixed_code = fixed_code.strip()
    if fixed_code.startswith("```"):
        lines = fixed_code.split("\n")
        fixed_code = "\n".join(lines[1:-1])

    return fixed_code


def generate_diff(
    file_path: str,
    original_code: str,
    fixed_code: str
) -> str:

    original_lines = original_code.splitlines(keepends=True)
    fixed_lines = fixed_code.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        lineterm=""
    )

    return "".join(diff)


def fix_agent(state: AgentState) -> AgentState:
    print("\n🔧 Fix Agent running...")

    proposed_fix = {}
    diff = {}

    for file_path in state["files_to_edit"]:

        if file_path not in state["file_contents"]:
            print(f"⚠️ Skipping {file_path} — content not available")
            continue

        print(f"✍️ Fixing file: {file_path}")

        current_code = state["file_contents"][file_path]

        fixed_code = generate_fix_for_file(
            file_path=file_path,
            current_code=current_code,
            fix_approach=state["fix_approach"],
            root_cause=state["root_cause"],
            issue_title=state["issue_title"]
        )

        # Safety check — if first line looks wrong reuse original
        first_line = fixed_code.split("\n")[0].strip()
        if first_line.endswith(".py"):
            print(f"⚠️ Bad output detected for {file_path}. Keeping original.")
            fixed_code = current_code

        file_diff = generate_diff(
            file_path=file_path,
            original_code=current_code,
            fixed_code=fixed_code
        )

        proposed_fix[file_path] = fixed_code
        diff[file_path] = file_diff

        print(f"✅ Fixed: {file_path}")

    print(f"\n✅ Fix Agent done — fixed {len(proposed_fix)} files")

    return {
        **state,
        "proposed_fix": proposed_fix,
        "diff": diff
    }

