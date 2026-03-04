# AI GitHub Agent 🤖

An autonomous multi-agent system that reads a GitHub issue,
researches the codebase, and plans a fix automatically.

## What It Does

- Agent 1 — Fetches issue details from GitHub
- Agent 2 — Searches codebase and finds relevant files
- Agent 3 — Identifies root cause and creates a fix plan
- Agent 4 — Writes the actual code fix (coming soon)
- Agent 5 — Tests the fix in Docker (coming soon)
- Agent 6 — Opens a Pull Request (coming soon)

## Tech Stack

- LangGraph — Agent orchestration
- LangChain — LLM tooling
- Sarvam AI — LLM for reasoning
- PyGithub — GitHub API
- FastAPI — Backend API