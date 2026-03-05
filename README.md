# AI GitHub Agent

## Workflow
This project is designed to automate interactions with GitHub using AI. It leverages machine learning algorithms to process GitHub data and provide insights or perform actions based on specific triggers.

## Tech Stack
- Node.js
- Express.js
- MongoDB
- GitHub API
- Docker

## Setup Instructions
1. Clone the repository: `git clone https://github.com/vikask011/ai-github-agent.git`
2. Navigate to the project directory: `cd ai-github-agent`
3. Install dependencies: `npm install`
4. Set up your environment variables as shown in the `.env.example` file.
5. Start the application: `npm start`

## API Endpoints
- **GET** `/api/v1/repos`: Fetch repository details.
- **POST** `/api/v1/actions`: Trigger an action on a repository.

## Notes
Ensure you have set the required API keys in your environment variables to interact with GitHub API successfully.

## Environment Variables
- `GITHUB_TOKEN`: Your GitHub personal access token.
- `MONGO_URI`: Connection string for MongoDB.
- `PORT`: Server port (default is 3000).