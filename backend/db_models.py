from pydantic import BaseModel, Field
from typing import List, Optional

class ApiExample(BaseModel):
    """Data model for a single API usage example."""
    user_query: str
    code: str

class ApiDoc(BaseModel):
    """Data model for a single API's documentation."""
    name: str
    description: str
    documentation_summary: Optional[str] = None
    base_url: str
    examples: List[ApiExample] = Field(..., min_length=1) 