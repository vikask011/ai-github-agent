from graph import graph
import uuid

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
    "should_proceed": True,
    "skip_reason": "",
    "test_passed": False,
    "test_output": "",
    "retry_count": 0,
    "pr_url": "",
    "branch_name": ""
}

thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

print("🚀 Starting AI GitHub Agent...\n")

result = graph.invoke(state, config)

print("\n" + "="*50)

# Case 1 — Validator stopped the graph
if not result.get("should_proceed", True):
    # Show correct message based on reason
    reason = result["skip_reason"]

    if "already" in reason.lower() or \
       "merged" in reason.lower() or \
       "closed" in reason.lower():
        print("✅ STOPPED — Issue Already Fixed")
    elif "not a code bug" in reason.lower():
        print("⚠️ STOPPED — Not A Fixable Code Issue")
    elif "no code files" in reason.lower():
        print("⚠️ STOPPED — No Code Files In Repo")
    else:
        print("🛑 STOPPED — Cannot Process Issue")

    print("="*50)
    print(f"Reason: {reason}")
    print("\nNo action taken. Exiting.")
    exit()

# Case 2 — Tests failed after max retries
if not result["test_passed"]:
    print("❌ STOPPED — Could not fix the issue")
    print("="*50)
    print(f"Test Output:\n{result['test_output'][:300]}")
    exit()

# Case 3 — Tests passed, ask for approval
print("⏸️  PAUSED — Waiting for your approval")
print("="*50)
print(f"Title:        {result['issue_title']}")
print(f"Root Cause:   {result['root_cause'][:150]}")
print(f"Files Fixed:  {list(result['proposed_fix'].keys())}")
print(f"Tests Passed: {result['test_passed']}")
print(f"\nTest Output:\n{result['test_output'][:300]}")

print("\n" + "="*50)
approval = input("👤 Create Pull Request? (yes/no): ")

if approval.lower() == "yes":
    print("\n▶️  Resuming → Creating PR...")
    final = graph.invoke(None, config)
    print("\n" + "="*50)
    print("🏁 DONE")
    print("="*50)
    print(f"PR URL: {final['pr_url']}")
    print("\nOpen the link above to review your PR.")
else:
    print("\n❌ PR creation cancelled.")
    print("No changes were made to the repository.")
