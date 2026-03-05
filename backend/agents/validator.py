from tools.github_client import get_repo, get_issue
from tools.sarvam_client import call_sarvam
from state import AgentState
import json

def parse_json_response(response: str) -> dict:
    response = response.strip()
    if "```" in response:
        lines = response.split("\n")
        cleaned = []
        for line in lines:
            if line.strip().startswith("```"):
                continue
            cleaned.append(line)
        response = "\n".join(cleaned).strip()
    return json.loads(response)


def check_issue_is_fixable(
    issue_title: str,
    issue_body: str
) -> dict:

    prompt = f"""
    You are a senior software engineer.
    
    Analyze this GitHub issue and determine 
    if it can be fixed by editing code in the repository.
    
    Issue Title: {issue_title}
    Issue Body: {issue_body}
    
    NOT fixable examples:
    - Missing files on local machine
    - Environment setup problems
    - npm/pip install errors on local machine
    - Permission errors on local machine
    - Hardware issues
    - Missing package.json on local machine
    - Local configuration problems
    - "works on my machine" type issues
    
    IS fixable examples:
    - Bug in a function
    - Missing error handling in code
    - Wrong logic in algorithm
    - Missing feature in existing code
    - Failing test cases
    - Security vulnerability in code
    
    
    
    Return ONLY a JSON object:
    {{
        "is_fixable": true or false,
        "reason": "explanation here"
    }}
    
    No explanation. Just the JSON.
    """

    try:
        response = call_sarvam(prompt)
        return parse_json_response(response)
    except Exception as e:
        print(f"⚠️ Fixable check failed: {e}")
        return {
            "is_fixable": True,
            "reason": "Could not determine — proceeding"
        }


def check_issue_already_fixed(
    repo_name: str,
    issue_number: int
) -> dict:

    try:
        repo = get_repo(repo_name)
        issue = get_issue(repo_name, issue_number)

        # Check 1 — Is issue already closed?
        if issue.state == "closed":
            return {
                "already_fixed": True,
                "reason": "Issue is already closed"
            }

        # Check 2 — Check comments for fix mentions
        try:
            comments = [
                c.body.lower()
                for c in issue.get_comments()
            ]
            fix_keywords = [
                "fixed", "resolved", "merged",
                "already fixed", "this is fixed",
                "closing", "duplicate"
            ]
            for comment in comments:
                for keyword in fix_keywords:
                    if keyword in comment:
                        return {
                            "already_fixed": True,
                            "reason": f"Comment suggests already fixed: '{keyword}' found"
                        }
        except Exception as e:
            print(f"⚠️ Comment check failed: {e}")

        # Check 3 — Check if linked PR exists and merged
        try:
            prs = list(repo.get_pulls(state="closed"))
            for pr in prs[:10]:
                body = pr.body or ""
                if f"#{issue_number}" in body or \
                   f"#{issue_number}" in pr.title:
                    return {
                        "already_fixed": True,
                        "reason": f"Merged PR found: {pr.html_url}"
                    }
        except Exception as e:
            print(f"⚠️ PR check failed: {e}")

        return {
            "already_fixed": False,
            "reason": "Issue still open — safe to fix"
        }

    except Exception as e:
        print(f"⚠️ GitHub check failed: {e}")
        return {
            "already_fixed": False,
            "reason": "Could not verify — proceeding"
        }


def verify_bug_still_exists(
    issue_title: str,
    issue_body: str,
    file_contents: dict[str, str]
) -> dict:

    try:
        files_summary = ""
        for path, content in file_contents.items():
            files_summary += f"\nFile: {path}\n{content[:1000]}\n"

        prompt = f"""
        You are a senior software engineer.
        
        GitHub Issue:
        Title: {issue_title}
        Body: {issue_body}
        
        Current code in the repository:
        {files_summary}
        
        Does the bug described in the issue
        still exist in the current code?
        
        Return ONLY a JSON object:
        {{
            "bug_exists": true or false,
            "confidence": "high" or "medium" or "low",
            "reason": "explanation here"
        }}
        
        No explanation. Just the JSON.
        """

        response = call_sarvam(prompt)
        return parse_json_response(response)

    except Exception as e:
        print(f"⚠️ Bug verification failed: {e}")
        return {
            "bug_exists": True,
            "confidence": "low",
            "reason": "Could not verify — proceeding"
        }


def check_repo_has_files(repo_name: str) -> dict:

    try:
        repo = get_repo(repo_name)
        contents = repo.get_contents("")

        # Wrap single file in list
        if not isinstance(contents, list):
            contents = [contents]

        # Added .html .css .scss .sass
        code_extensions = (
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".java", ".cpp", ".c", ".go", ".rb"
        )

        has_code = False
        while contents:
            file = contents.pop(0)
            if file.type == "dir":
                try:
                    sub = repo.get_contents(file.path)
                    if not isinstance(sub, list):
                        sub = [sub]
                    contents.extend(sub)
                except:
                    continue
            elif file.path.endswith(code_extensions):
                has_code = True
                break

        if not has_code:
            return {
                "has_files": False,
                "reason": "Repository has no code files to fix"
            }

        return {
            "has_files": True,
            "reason": "Repository has code files"
        }

    except Exception as e:
        print(f"⚠️ Repo check failed: {e}")
        return {
            "has_files": True,
            "reason": "Could not verify — proceeding"
        }


def validator_agent(state: AgentState) -> AgentState:
    print("\n🛡️ Validator Agent running...")

    try:
        from urllib.parse import urlparse
        parts = urlparse(
            state["issue_url"]
        ).path.strip("/").split("/")
        repo_name = f"{parts[0]}/{parts[1]}"
        issue_number = int(parts[3])

        # Check 0 — Is this a fixable issue?
        print("🔍 Checking if issue is fixable...")
        fixable_check = check_issue_is_fixable(
            state["issue_title"],
            state["issue_body"]
        )

        if not fixable_check["is_fixable"]:
            print(f"⚠️ Not fixable: {fixable_check['reason']}")
            return {
                **state,
                "should_proceed": False,
                "skip_reason": f"Not a code bug: {fixable_check['reason']}"
            }

        print("✅ Issue is fixable")

        # Check 1 — Does repo have code files?
        print("🔍 Checking repo has code files...")
        repo_check = check_repo_has_files(repo_name)

        if not repo_check["has_files"]:
            print(f"⚠️ No code files: {repo_check['reason']}")
            return {
                **state,
                "should_proceed": False,
                "skip_reason": repo_check["reason"]
            }

        print("✅ Repo has code files")

        # Check 2 — Already fixed?
        print("🔍 Checking if already fixed...")
        github_check = check_issue_already_fixed(
            repo_name,
            issue_number
        )

        if github_check["already_fixed"]:
            print(f"⚠️ Already fixed: {github_check['reason']}")
            return {
                **state,
                "should_proceed": False,
                "skip_reason": github_check["reason"]
            }

        print("✅ Issue still open")

        # Check 3 — Bug still in code?
        if state.get("file_contents"):
            print("🔍 Verifying bug exists in code...")
            code_check = verify_bug_still_exists(
                state["issue_title"],
                state["issue_body"],
                state["file_contents"]
            )

            print(f"Bug exists: {code_check['bug_exists']}")
            print(f"Confidence: {code_check['confidence']}")
            print(f"Reason: {code_check['reason']}")

            if not code_check["bug_exists"] and \
               code_check["confidence"] == "high":
                return {
                    **state,
                    "should_proceed": False,
                    "skip_reason": f"Bug not in code: {code_check['reason']}"
                }

        print("✅ All checks passed — proceeding")
        return {
            **state,
            "should_proceed": True,
            "skip_reason": ""
        }

    except Exception as e:
        print(f"⚠️ Validator error: {e}")
        print("⚠️ Proceeding despite error")
        return {
            **state,
            "should_proceed": True,
            "skip_reason": ""
        }