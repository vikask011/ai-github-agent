from tools.sarvam_client import call_sarvam
from state import AgentState
import difflib

def clean_code_response(response: str) -> str:
    response = response.strip()
    if "```" in response:
        lines = response.split("\n")
        cleaned = []
        inside_block = False
        for line in lines:
            if line.strip().startswith("```"):
                inside_block = not inside_block
                continue
            if not inside_block:
                cleaned.append(line)
        response = "\n".join(cleaned).strip()
    return response


def is_valid_python(code: str) -> bool:
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False


def generate_fix_for_file(
    file_path: str,
    current_code: str,
    fix_approach: str,
    root_cause: str,
    issue_title: str,
    previous_error: str = ""
) -> str:

    error_context = ""
    if previous_error:
        error_context = f"""
    PREVIOUS ATTEMPT FAILED WITH THIS ERROR:
    {previous_error}
    Fix these specific errors in this attempt.
    """

    prompt = f"""
    You are a senior software engineer.
    Fix the bug in this file.
    
    Issue: {issue_title}
    Root Cause: {root_cause}
    
    Fix Plan:
    {fix_approach}
    
    Current code in {file_path}:
    {current_code}
    
    {error_context}
    
    CRITICAL RULES:
    - Return the COMPLETE file
    - Keep ALL existing code structure
    - Only change what is needed to fix the bug
    - Return ONLY raw code
    - No markdown, no backticks, no explanation
    """

    fixed_code = call_sarvam(prompt)
    fixed_code = clean_code_response(fixed_code)

    # Only validate Python files
    if file_path.endswith(".py"):
        if not is_valid_python(fixed_code):
            print(f"⚠️ Invalid Python generated. Keeping original.")
            return current_code
        first_line = fixed_code.split("\n")[0].strip()
        if first_line.endswith(".py"):
            print(f"⚠️ Bad output detected. Keeping original.")
            return current_code

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

    previous_error = state.get("test_output", "")

    for file_path in state["files_to_edit"]:

        if file_path not in state["file_contents"]:
            print(f"⚠️ Skipping {file_path} — not available")
            continue

        print(f"✍️ Fixing file: {file_path}")

        current_code = state["file_contents"][file_path]

        fixed_code = generate_fix_for_file(
            file_path=file_path,
            current_code=current_code,
            fix_approach=state["fix_approach"],
            root_cause=state["root_cause"],
            issue_title=state["issue_title"],
            previous_error=previous_error
        )

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