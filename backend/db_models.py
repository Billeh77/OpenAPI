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
    examples: List[ApiExample]

class McpServerDoc(BaseModel):
    """Data model for a single MCP Server's documentation."""
    name: str
    description: str
    repository_url: str
    # Type helps the LLM choose the right base image and install commands.
    installation_type: str  # e.g., 'python', 'node', 'docker'
    documentation_summary: Optional[str] = None
    # We'll use this to prompt the user later if needed.
    required_env_vars: Optional[List[str]] = Field(default_factory=list) 