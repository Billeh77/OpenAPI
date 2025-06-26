# Universal MCP Adapter

This project is a proof-of-concept for an intelligent MCP (Model Context Protocol) server deployment system. It's a full-stack application with a FastAPI backend and a React frontend that allows users to make natural language requests for MCP servers, which are then automatically containerized and deployed using Docker.

## 🚀 How to Run the Project

**Prerequisites:**
- Docker must be installed and running on your system
- Python 3.10+ for the backend
- Node.js 18+ for the frontend

You will need two separate terminal windows to run both the backend server and the frontend application.

### 1. Run the Backend Server

First, set up and activate a Python virtual environment, install the dependencies, and start the FastAPI server.

```bash
# Navigate to the backend directory
cd backend

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the required packages
pip install -r requirements.txt

# Start the FastAPI server (it will run on http://localhost:8000)
uvicorn main:app --reload --port 8000
```

### 2. Run the Frontend Application

In a second terminal, navigate to the frontend directory, install the npm packages, and start the Vite development server.

```bash
# Navigate to the frontend directory
cd frontend

# Install npm dependencies
npm install

# Start the React development server (it will run on http://localhost:5173)
npm run dev
```

### 3. Open the Application

Once both servers are running, open your web browser and navigate to:

**[http://localhost:5173](http://localhost:5173)**

You should see the chat interface, ready to accept your queries!

## 💡 Example Queries

Try asking for MCP servers like:
- "I need a tool to manage files"
- "I want to work with Git repositories" 
- "Set up a filesystem server for me"
- "Deploy a Git MCP server"

The system will:
1. Find the most relevant MCP server using semantic search
2. Generate a Dockerfile to containerize it
3. Build and run the container automatically
4. Provide you with a connection URL to access the server 