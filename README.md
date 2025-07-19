# Universal API Demo

This project is a proof-of-concept for an "API for APIs". It's a full-stack application with a FastAPI backend and a React frontend that allows a user to make natural language queries, which are then translated into live API calls by an agentic backend.

## How to Run the Project

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

## Example Queries

Try asking things like:
- "What's the weather in New York?" or "weather in 52.5, 13.4"
- "Tell me about France"
- "What's the price of bitcoin?"
- "Tell me a joke"
- "I'm bored"
- "Give me a cat fact"
- "I need some advice"
- "Tell me about the number 100"
- "What are the public holidays in Germany this year?" (e.g., "holidays in DE 2024")
- "What is my IP address?" 
