from fastapi import APIRouter
from pydantic import BaseModel
from agent import pick_api, build_code, run_code

router = APIRouter()

class ChatIn(BaseModel):
    message: str

@router.post("/chat")
def chat(in_: ChatIn):
    api = pick_api(in_.message)
    if not api:
        return {"error": "No matching API could be found for your query."}
    
    try:
        code = build_code(api, in_.message)
        output = run_code(code)
        return {"api": api, "code": code, "result": output}
    except Exception as e:
        # This will catch errors like template not found, etc.
        return {"error": f"An error occurred: {str(e)}"} 