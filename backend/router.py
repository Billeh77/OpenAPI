from fastapi import APIRouter
from pydantic import BaseModel
import agent

router = APIRouter()

class ChatIn(BaseModel):
    message: str

@router.post("/chat")
def chat(payload: ChatIn):
    """
    Receives a user's message, passes it to the agent,
    and returns the agent's response.
    """
    if not payload.message:
        return {"error": "Message cannot be empty."}
        
    response = agent.handle_query(payload.message)
    
    return response 