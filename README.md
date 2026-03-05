# 🤖 AI GitHub Agent

An autonomous multi-agent system built with **LangGraph** and **Sarvam AI** that resolves GitHub issues end-to-end.  
It researches the codebase, plans a fix, verifies it in Docker, and opens a PR with **human-in-the-loop approval**.

---

# 🎯 Key Features

- **Autonomous Research:** Uses RAG to find and read relevant files based on an issue URL.  
- **Intelligent Validation:** Detects if an issue is already fixed or out of scope before wasting tokens.  
- **Dockerized Testing:** Automatically runs `pytest` in an isolated container to verify the fix.  
- **Human-in-the-Loop:** Pauses the graph and waits for your approval via API before creating a Pull Request.  
- **Stateful Retries:** Powered by LangGraph for robust error handling and cyclic reasoning.

---

# 🏗️ The Workflow

1. **Fetch:** Extracts metadata from the GitHub issue URL.  
2. **Research:** Explores the repository to locate the root cause.  
3. **Plan:** Generates a step-by-step implementation strategy.  
4. **Fix:** Writes the actual code changes using Sarvam AI.  
5. **Test:** Executes the test suite in a Sandbox Docker environment.  
6. **Review:** Pauses for human confirmation of the plan and diff.  
7. **Ship:** Creates a new branch and opens a PR on GitHub.

---

# 🔧 Tech Stack

| Component | Technology |
|----------|-----------|
| Orchestration | LangGraph (Stateful Agent Workflows) |
| LLM | Sarvam AI (Reasoning & Code Gen) |
| Interface | FastAPI |
| Integrations | PyGithub & Docker SDK |

---

# 🚀 Quick Start

## 1. Installation

```bash
git clone https://github.com/your-username/ai-github-agent
cd ai-github-agent
pip install -r requirements.txt
```

## 2. Configure Environment

Create a `.env` file in the root directory:

```bash
GITHUB_TOKEN=your_personal_access_token
SARVAM_API_KEY=your_sarvam_api_key
```

## 3. Run the Agent

Make sure Docker Desktop is running, then start the system:

```bash
# Run via CLI script
python backend/test_agent.py

# Or start the API server
uvicorn backend.main:app --reload
```

---

# 📡 API Reference

## POST /solve

Payload:

```json
{ "issue_url": "https://github.com/user/repo/issues/1" }
```

Starts the agent. Returns a `thread_id` to track progress.

---

## POST /approve-pr

Payload:

```json
{ "thread_id": "uuid" }
```

Signals the agent to proceed with opening the Pull Request.
