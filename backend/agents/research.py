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
        keywords = json.loads(response)
        return keywords
    except:
        return issue_title.lower().split()


def search_relevant_files(repo_name: str, keywords: list[str]) -> list[str]:
    relevant_files = []
    seen = set()

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
    
    These files were found in the codebase:
    {file_list}
    
    Pick the TOP 3 most relevant files 
    that likely need to be changed to fix this issue.
    
    Return ONLY a JSON array of file paths like:
    ["path/to/file1.py", "path/to/file2.py"]
    
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
        return top_files
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