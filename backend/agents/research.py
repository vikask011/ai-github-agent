from tools.github_client import get_repo, search_code_in_repo
from tools.sarvam_client import call_sarvam
from state import AgentState
import json

def extract_keywords(issue_title: str, issue_body: str) -> list[str]:
    prompt = f"""
    Extract 5-8 technical keywords from this GitHub issue
    that can be used to search for relevant code files.
    
    Issue Title: {issue_title}
    Issue Body: {issue_body}
    
    Return ONLY a JSON array of keywords like:
    ["keyword1", "keyword2", "keyword3"]
    
    No explanation. Just the JSON array.
    """
    response = call_sarvam(prompt)
    response = response.strip()
    if "```" in response:
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    try:
        return json.loads(response)
    except:
        return issue_title.lower().split()


def get_all_repo_files(repo_name: str) -> list[str]:
    # Get ALL files directly from repo
    # No search needed — works for small repos
    repo = get_repo(repo_name)
    contents = repo.get_contents("")
    files = []

    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            # Go into subdirectories
            contents.extend(repo.get_contents(file_content.path))
        else:
            # Only include code files
            if file_content.path.endswith((
                ".py", ".js", ".ts", ".java",
                ".go", ".rb", ".cpp", ".c"
            )):
                files.append(file_content.path)

    return files


def search_relevant_files(repo_name: str, keywords: list[str]) -> list[str]:
    relevant_files = []
    seen = set()

    # First try GitHub code search
    for keyword in keywords[:5]:
        try:
            results = search_code_in_repo(repo_name, keyword)
            for file in list(results)[:3]:
                if file.path not in seen:
                    seen.add(file.path)
                    relevant_files.append(file.path)
            print(f"✅ Found files for '{keyword}'")
        except Exception as e:
            print(f"⚠️ Search failed for '{keyword}': {e}")
            continue

    # If search returned nothing → get all repo files directly
    if not relevant_files:
        print("⚠️ Search returned empty. Getting all repo files directly...")
        relevant_files = get_all_repo_files(repo_name)
        print(f"✅ Found {len(relevant_files)} files in repo")

    return relevant_files[:10]


def read_file_contents(repo_name: str, file_paths: list[str]) -> dict[str, str]:
    repo = get_repo(repo_name)
    file_contents = {}

    for path in file_paths:
        try:
            content = repo.get_contents(path)
            file_contents[path] = content.decoded_content.decode("utf-8")
            print(f"📄 Read file: {path}")
        except Exception as e:
            print(f"⚠️ Could not read file {path}: {e}")
            continue

    return file_contents


def pick_most_relevant_files(
    issue_title: str,
    issue_body: str,
    file_contents: dict[str, str]
) -> list[str]:

    file_list = "\n".join(file_contents.keys())

    prompt = f"""
    Given this GitHub issue:
    Title: {issue_title}
    Body: {issue_body}
    
    These files exist in the codebase:
    {file_list}
    
    Pick the TOP 3 most relevant files
    that likely need to be changed to fix this issue.
    
    IMPORTANT: Only return file paths from the list above.
    Do not make up or guess file paths.
    
    Return ONLY a JSON array like:
    ["exact/path/from/above.py"]
    
    No explanation. Just the JSON array.
    """

    response = call_sarvam(prompt)
    response = response.strip()
    if "```" in response:
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]

    try:
        top_files = json.loads(response)
        # Validate — only return files that actually exist
        valid_files = [
            f for f in top_files
            if f in file_contents
        ]
        # If validation fails fallback to all files
        if not valid_files:
            return list(file_contents.keys())[:3]
        return valid_files
    except:
        return list(file_contents.keys())[:3]


def research_agent(state: AgentState) -> AgentState:
    print("\n🔍 Research Agent running...")

    print("🔑 Extracting keywords...")
    keywords = extract_keywords(
        state["issue_title"],
        state["issue_body"]
    )
    print(f"✅ Keywords: {keywords}")

    print("🔎 Searching codebase...")
    relevant_files = search_relevant_files(
        state["repo_name"],
        keywords
    )
    print(f"✅ Found files: {relevant_files}")

    print("📖 Reading file contents...")
    file_contents = read_file_contents(
        state["repo_name"],
        relevant_files
    )

    print("🧠 Picking most relevant files...")
    top_files = pick_most_relevant_files(
        state["issue_title"],
        state["issue_body"],
        file_contents
    )
    print(f"✅ Top relevant files: {top_files}")

    top_file_contents = {
        path: file_contents[path]
        for path in top_files
        if path in file_contents
    }

    return {
        **state,
        "keywords": keywords,
        "relevant_files": top_files,
        "file_contents": top_file_contents
    }
