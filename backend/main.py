from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router

app = FastAPI(
    title="Universal API Demo",
    description="An agentic API that writes and executes code to call other APIs on the fly.",
    version="0.1.0",
)

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True, 
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Universal API Demo. Send POST requests to /chat."} 