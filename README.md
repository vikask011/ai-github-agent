# AI GitHub Agent

## What It Does
AI GitHub Agent automates interactions with GitHub, enabling developers to manage repositories, issues, and pull requests efficiently through AI-driven commands.

## Architecture
The architecture of AI GitHub Agent is modular and consists of various components that manage requests, authentication, data processing, and user interaction.

## Tech Stack
- **Languages**: Python, JavaScript
- **Frameworks**: Flask, React
- **Database**: PostgreSQL
- **Cloud**: AWS

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/vikask011/ai-github-agent.git
   cd ai-github-agent
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables by creating a `.env` file and adding your GitHub API credentials.

## Environment Variables
- `GITHUB_TOKEN`: Your GitHub personal access token.
- `FLASK_ENV`: Set to `development` for local development.

## API Endpoints
- `GET /api/repos`: List all repositories.
- `POST /api/issues`: Create a new issue.
- `PUT /api/pulls`: Update a pull request.

## Requirements
- Python 3.8+
- Flask
- PostgreSQL
- Requests library

## Notes
- Make sure to handle API rate limits when making requests to GitHub's API.
- Always validate user input to avoid security vulnerabilities.