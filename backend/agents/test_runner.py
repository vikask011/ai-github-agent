from tools.docker_runner import run_tests_in_docker
from state import AgentState

MAX_RETRIES = 3

def test_runner_agent(state: AgentState) -> AgentState:
    print("\n🧪 Test Runner Agent running...")

    # Check if any Python files in the fix
    has_python = any(
        f.endswith(".py")
        for f in state["proposed_fix"].keys()
    )

    if not has_python:
        print("⚠️ No Python files detected")
        print("✅ Skipping tests — non-Python project")
        return {
            **state,
            "test_passed": True,
            "test_output": "Tests skipped — non-Python project"
        }

    # Python files — run pytest in Docker
    retry_count = state.get("retry_count", 0)

    if retry_count >= MAX_RETRIES:
        print(f"❌ Max retries ({MAX_RETRIES}) reached.")
        return {
            **state,
            "test_passed": False,
            "test_output": "Max retries reached."
        }

    print(f"🔄 Attempt {retry_count + 1} of {MAX_RETRIES}")

    result = run_tests_in_docker(
        proposed_fix=state["proposed_fix"],
        original_files=state["file_contents"]
    )

    test_passed = result["passed"]
    test_output = result["output"]

    if test_passed:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed on attempt {retry_count + 1}")
        print(f"Output: {test_output[:300]}")

    return {
        **state,
        "test_passed": test_passed,
        "test_output": test_output,
        "retry_count": retry_count + 1
    }