from github import Github
from dotenv import load_dotenv
import os

load_dotenv()

def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    return Github(token)

def get_repo(repo_name: str):
    g = get_github_client()
    return g.get_repo(repo_name)

def get_issue(repo_name: str, issue_number: int):
    repo = get_repo(repo_name)
    return repo.get_issue(issue_number)

def search_code_in_repo(repo_name: str, keyword: str):
    g = get_github_client()
    # Correct way to search code in PyGithub
    query = f"{keyword} repo:{repo_name}"
    results = g.search_code(query)
    return results