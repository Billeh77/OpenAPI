import anthropic
import os
import re
import json

# Initialize the client from the environment variable
try:
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
except KeyError:
    # This allows the app to start even if the key is not set,
    # but it will fail when an LLM call is made.
    client = None 
    print("Warning: CLAUDE_API_KEY environment variable not set.")

# Few-shot examples to guide the LLM in generating correct code.
# This helps it understand the expected output format.
FEW_SHOT_EXAMPLES = """
<example>
<user_query>
Tell me a joke
</user_query>
<api_documentation>
name: JokeAPI
description: Fetches a random joke. It can be a single-part joke or a two-part joke (setup and delivery). The user query would be something like "tell me a joke".
base_url: https://v2.jokeapi.dev/joke/Any
example: |
  import httpx, json
  # User query was "tell me a random joke"
  resp = httpx.get("https://v2.jokeapi.dev/joke/Any", timeout=5)
  print(json.dumps(resp.json(), indent=2))
</api_documentation>
<thinking>
The user wants a joke. The JokeAPI is perfect for this. The documentation shows a simple GET request to a URL. I will write Python code to perform this GET request using the httpx library and print the JSON response. The user's query is simple and doesn't require any parameters.
</thinking>
<code>
import httpx, json

print("Fetching a random joke...")
try:
    resp = httpx.get("https://v2.jokeapi.dev/joke/Any", timeout=5)
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
</code>
</example>
<example>
<user_query>
what are the holidays in Canada for 2025?
</user_query>
<api_documentation>
name: Nager.Date Public Holidays
description: Fetches the public holidays for a given year and country code. You need to extract a year (e.g., 2024) and a two-letter country code (e.g., US, DE, FR) from the user's query.
base_url: https://date.nager.at/api/v3/PublicHolidays
example: |
  import httpx, json
  # User query was "what are the holidays in Canada for 2025?"
  year = "2025"
  country_code = "CA"
  resp = httpx.get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}", timeout=10)
  print(json.dumps(resp.json(), indent=2))
</api_documentation>
<thinking>
The user wants public holidays for a specific country (Canada) and year (2025). The Nager.Date API is designed for this. I need to extract the year '2025' and the country code 'CA' from the user's query. The documentation provides the base URL structure. I will construct the full URL, make a GET request, and print the JSON response.
</thinking>
<code>
import httpx, json

print("Fetching public holidays for CA in 2025...")
try:
    year = "2025"
    country_code = "CA"
    resp = httpx.get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}", timeout=10)
    resp.raise_for_status()
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(json.dumps({"error": str(e)}))
</code>
</example>
"""

# Comprehensive system prompt with deep MCP knowledge
SYSTEM_PROMPT = """
You are an expert DevOps engineer and MCP protocol specialist. You have comprehensive knowledge of the Model Context Protocol (MCP), its architecture, implementation patterns, and containerization requirements.

**DEEP MCP PROTOCOL KNOWLEDGE:**

**What is MCP?**
Model Context Protocol (MCP) is an open standard that enables AI assistants to securely connect to external data sources and tools. MCP servers provide "tools", "resources", and "prompts" that AI assistants can discover and use.

**MCP Architecture:**
- **Client-Server Model**: AI assistant (client) connects to MCP server
- **Communication**: JSON-RPC 2.0 over stdio (stdin/stdout), NOT HTTP
- **Protocol Flow**: Initialize → Discover Capabilities → Use Tools
- **Bidirectional**: Both client and server can send requests

**MCP Protocol Handshake:**
1. Client sends "initialize" request with protocol version and capabilities
2. Server responds with its capabilities (tools, resources, prompts)
3. Client sends "initialized" notification
4. Server is ready to handle tool calls, resource reads, etc.

**MCP Message Types:**
- `initialize` - Protocol handshake
- `initialized` - Handshake completion notification  
- `tools/list` - Discover available tools
- `tools/call` - Execute a specific tool
- `resources/list` - List available resources
- `resources/read` - Read a specific resource
- `prompts/list` - List available prompts
- `prompts/get` - Get a specific prompt

**MCP Server Implementation Patterns:**
- **Entry Points**: MCP servers are CLI applications with entry points like `mcp-server-git`
- **Installation**: Usually via `pip install .` from pyproject.toml
- **Dependencies**: Common deps include `mcp`, `pydantic`, `click`, `asyncio`
- **Repository Structure**: Often in monorepos like `modelcontextprotocol/servers`

**Critical MCP Deployment Requirements:**
1. **MCP servers are NOT web services** - they're CLI tools expecting stdin/stdout
2. **JSON-RPC Protocol** - All communication uses JSON-RPC 2.0 format
3. **Process Management** - Must run as subprocess with pipe communication
4. **Protocol Bridge** - Need HTTP-to-MCP bridge for web access
5. **Proper Initialization** - Must handle MCP handshake sequence

**MCP-to-HTTP Bridge Requirements:**
- Run MCP server as subprocess with stdin/stdout pipes
- Implement JSON-RPC client for MCP communication
- Handle MCP initialization sequence properly
- Translate HTTP requests to MCP tool calls
- Provide REST endpoints for tool discovery and execution
- Handle errors, timeouts, and process management

**CONTEXT & ARCHITECTURE:**
You are operating within a Universal MCP Adapter system that:
- Receives natural language requests for MCP functionality (e.g., "I need file management tools")
- Uses RAG to find relevant MCP servers from a knowledge base
- Generates Dockerfiles to containerize these MCP servers automatically
- Builds and runs containers to provide HTTP endpoints for MCP server access
- Has retry logic that will provide you with previous failed attempts and errors

**MCP SERVER KNOWLEDGE:**
- MCP servers are typically Python applications that implement the Model Context Protocol
- They usually have a main.py or server.py entry point
- Many MCP servers use dependencies like `mcp`, `pydantic`, `httpx`, `asyncio`
- MCP servers may not have requirements.txt files - you need to analyze the code and install dependencies manually
- Common MCP server patterns: they listen on stdin/stdout by default, but we need HTTP endpoints
- MCP servers often need to be wrapped with HTTP servers (like `uvicorn` for FastAPI-based servers)

**COMMON FAILURE SCENARIOS & SOLUTIONS:**
1. **"No module named 'git.server'"**: MCP servers don't have importable modules - use CLI entry points
2. **"Could not import module 'server'"**: MCP servers are CLI tools, not web apps - create bridge
3. **Missing requirements.txt**: Use pyproject.toml with `pip install .` or `uv sync`
4. **Wrong entry point**: Use the CLI command from pyproject.toml scripts (e.g., `mcp-server-git`)
5. **MCP servers expecting stdin/stdout**: This is CORRECT - create bridge to handle JSON-RPC protocol
6. **Missing system dependencies**: Install git, curl, uv as needed
7. **Port binding issues**: Bridge server must bind to 0.0.0.0:8080
8. **Protocol mismatch**: MCP uses JSON-RPC over stdio - HTTP bridge is mandatory

**DOCKERFILE GENERATION RULES:**
1. **OUTPUT ONLY DOCKERFILE CONTENT** - No markdown, no explanations, no thinking blocks in final output
2. **Use the OFFICIAL Dockerfile approach** - MCP servers often have their own Dockerfiles
3. **Install system dependencies**: git, curl, uv (modern Python package manager)
4. **Clone the repository** to /app directory
5. **Navigate to correct subdirectory** if the MCP server is in a subfolder
6. **Use the official installation method**:
   - Check for existing Dockerfile first and adapt it
   - Use `uv sync` for modern Python packaging
   - Install with `pip install .` if pyproject.toml exists
7. **Create MCP-to-HTTP bridge** - MCP servers communicate via stdin/stdout, not HTTP
8. **Install bridge dependencies**: `pip install fastapi uvicorn asyncio`
9. **EXPOSE 8080** - this is critical for our system
10. **Create a bridge script** that runs the MCP server and translates HTTP to MCP protocol
11. **Use proper CMD** that starts the bridge server on 0.0.0.0:8080

**CRITICAL MCP KNOWLEDGE:**
- MCP servers are CLI tools with entry points like `mcp-server-git`
- They communicate via JSON-RPC over stdin/stdout, NOT HTTP
- You MUST create a bridge that runs the MCP server as subprocess and handles protocol translation
- The bridge receives HTTP requests and sends JSON-RPC to the MCP server via stdin
- The bridge reads JSON-RPC responses from the MCP server's stdout and returns HTTP responses

**CHAIN OF THOUGHT PROCESS:**
Before generating the Dockerfile, think through:
1. What type of MCP server is this? (filesystem, git, database, etc.)
2. What's the repository structure? Is the server in a subdirectory?
3. What dependencies does it likely need based on its functionality?
4. Does it have standard Python packaging files?
5. How should it be started to provide HTTP access on port 8080?
6. What system packages might be needed for its functionality?

Think step-by-step inside `<thinking>` tags, then provide ONLY the Dockerfile content.
"""

def _extract_code(response_text: str) -> str:
    """
    Robustly extracts Python code from the LLM's response.
    It removes <thinking> blocks and markdown fences.
    """
    # First, remove the thinking block entirely
    response_text = re.sub(r"<thinking>.*?</thinking>", "", response_text, flags=re.DOTALL)
    
    # Then, look for a code block. If not found, assume the whole response is code.
    match = re.search(r"```(?:python)?\n(.*)```", response_text, re.DOTALL)
    if match:
        code = match.group(1)
    else:
        code = response_text

    return code.strip()


def _parse_deployment_package(response_text: str) -> dict:
    """
    Parses the LLM response to extract deployment package files.
    Expects JSON format or falls back to extracting individual files.
    """
    # Remove thinking blocks
    response_text = re.sub(r"<thinking>.*?</thinking>", "", response_text, flags=re.DOTALL)
    
    # Try to parse as JSON first
    try:
        # Look for JSON block
        json_match = re.search(r"```json\n(.*?)```", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object in the response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in response")
        
        deployment_files = json.loads(json_str)
        
        # Validate required files
        required_files = ["Dockerfile", "mcp_bridge.py", "requirements.txt", "entrypoint.sh", "health_check.py"]
        for required_file in required_files:
            if required_file not in deployment_files:
                raise ValueError(f"Missing required file: {required_file}")
        
        return deployment_files
        
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Failed to parse JSON deployment package: {e}")
        
        # Fallback: try to extract individual files from markdown blocks
        files = {}
        
        # Extract Dockerfile
        dockerfile_match = re.search(r"```dockerfile\n(.*?)```", response_text, re.DOTALL | re.IGNORECASE)
        if dockerfile_match:
            files["Dockerfile"] = dockerfile_match.group(1).strip()
        
        # Extract Python files
        python_matches = re.finditer(r"```python\n(.*?)```", response_text, re.DOTALL)
        for i, match in enumerate(python_matches):
            if i == 0:
                files["mcp_bridge.py"] = match.group(1).strip()
            elif i == 1:
                files["health_check.py"] = match.group(1).strip()
        
        # Extract shell script
        bash_match = re.search(r"```bash\n(.*?)```", response_text, re.DOTALL)
        if bash_match:
            files["entrypoint.sh"] = bash_match.group(1).strip()
        
        # Add default files if missing
        if "requirements.txt" not in files:
            files["requirements.txt"] = "fastapi==0.104.1\nuvicorn[standard]==0.24.0\npydantic==2.5.0\nhttpx==0.25.2"
        
        if "docker-compose.yml" not in files:
            files["docker-compose.yml"] = "version: '3.8'\nservices:\n  mcp-server:\n    build: .\n    ports:\n      - '8080:8080'"
        
        if "README.md" not in files:
            files["README.md"] = "# MCP Server Deployment\n\nGenerated automatically."
        
        # Ensure we have at least a Dockerfile
        if "Dockerfile" not in files:
            raise ValueError("Could not extract Dockerfile from LLM response")
        
        return files

def generate_deployment_package(user_query: str, retrieved_docs: list[dict]) -> dict:
    """Generates complete deployment package with multiple files for MCP server."""
    if not client:
        raise ValueError("Anthropic client is not initialized. Please set the CLAUDE_API_KEY.")

    docs_json_str = json.dumps(retrieved_docs, indent=2)
    
    prompt = f"""
    Generate a COMPLETE deployment package for the requested MCP server. You must generate ALL required files for successful deployment.

    User's Request: {user_query}
    MCP Server Documentation:
{docs_json_str}

    **REQUIRED OUTPUT FORMAT:**
    Return a JSON object with the following structure:
    {{
        "Dockerfile": "# Complete Dockerfile content here",
        "mcp_bridge.py": "# Complete MCP-to-HTTP bridge implementation",
        "requirements.txt": "# Bridge dependencies",
        "entrypoint.sh": "#!/bin/bash\\n# Startup script",
        "health_check.py": "# Health monitoring script",
        "docker-compose.yml": "# Docker compose configuration",
        "README.md": "# Deployment documentation"
    }}

    **CRITICAL REQUIREMENTS:**
    1. **Dockerfile**: Must install MCP server, create bridge, expose port 8080
    2. **mcp_bridge.py**: Complete HTTP-to-MCP bridge using the template I provided
    3. **requirements.txt**: FastAPI, uvicorn, pydantic, httpx for bridge
    4. **entrypoint.sh**: Startup script that validates MCP server and starts bridge
    5. **health_check.py**: HTTP health check for container monitoring
    6. **docker-compose.yml**: Complete service definition
    7. **README.md**: Usage documentation with API endpoints

    **MCP BRIDGE IMPLEMENTATION:**
    The mcp_bridge.py MUST:
    - Import the MCP bridge template from the codebase
    - Customize the server_command for the specific MCP server
    - Handle MCP protocol initialization and tool discovery
    - Expose HTTP endpoints for tool calling
    - Include proper error handling and logging

    **DOCKERFILE REQUIREMENTS:**
    - Use python:3.12-slim-bookworm base image
    - Install system dependencies (git, curl, build-essential)
    - Clone MCP server repository
    - Navigate to correct subdirectory
    - Install MCP server dependencies (pip install . or uv sync)
    - Copy ALL bridge files (mcp_bridge.py, requirements.txt, entrypoint.sh, health_check.py)
    - Install bridge dependencies
    - Make scripts executable
    - Expose port 8080
    - Add health check
    - Use entrypoint.sh as ENTRYPOINT

    Generate a complete, production-ready deployment package as JSON.
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,  # Increased for multiple files
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text
    
    return _parse_deployment_package(message)


def generate_deployment_package_with_retry(old_deployment_files: dict, error: str, user_query: str, retrieved_docs: list[dict], error_history: list = None) -> dict:
    """Attempts to fix broken deployment package given the error it produced and the original context."""
    if not client:
        raise ValueError("Anthropic client is not initialized. Please set the CLAUDE_API_KEY.")

    if error_history is None:
        error_history = []

    print(f"--- Deployment failed. Retrying with error: {error} ---")
    
    docs_json_str = json.dumps(retrieved_docs, indent=2)
    error_history_str = "\n".join([f"Attempt {i+1}: {err}" for i, err in enumerate(error_history)])
    
    prompt = f"""
**RETRY CONTEXT:**
You are fixing a FAILED MCP server deployment. The previous attempt failed and you must learn from the specific errors.

**ORIGINAL USER REQUEST:**
{user_query}

**MCP SERVER DOCUMENTATION:**
{docs_json_str}

**PREVIOUS FAILED DEPLOYMENT FILES:**
{json.dumps(old_deployment_files, indent=2)}

**CURRENT ERROR:**
```
{error}
```

**PREVIOUS ERROR HISTORY:**
{error_history_str}

**CRITICAL ERROR ANALYSIS:**
You must identify and fix the root cause. Common MCP deployment failures:

1. **MCP Protocol Errors**: 
   - "No module named 'git.server'" → MCP servers are CLI tools, not importable modules
   - Use subprocess to run CLI commands like "mcp-server-git"
   - Don't try to import MCP server code directly

2. **Container Startup Failures**:
   - "Container failed to start" → Check MCP server binary availability
   - Ensure proper working directory and file permissions
   - Verify MCP server can be executed as CLI command

3. **Bridge Implementation Issues**:
   - Bridge must run MCP server as subprocess with stdin/stdout communication
   - Implement proper JSON-RPC protocol handling
   - Handle MCP initialization handshake correctly

4. **Dependency Problems**:
   - Missing system packages (git, curl, build-essential)
   - Wrong Python dependencies or versions
   - MCP server not properly installed

5. **Port Binding Issues**:
   - Bridge must bind to 0.0.0.0:8080, not localhost
   - Container health checks must work properly

**REQUIRED OUTPUT FORMAT:**
Return a JSON object with ALL files needed for successful deployment:
{{
    "Dockerfile": "# Fixed Dockerfile addressing the specific error",
    "mcp_bridge.py": "# Complete working MCP-to-HTTP bridge",
    "requirements.txt": "# All required dependencies",
    "entrypoint.sh": "#!/bin/bash\\n# Robust startup script with error checking",
    "health_check.py": "# Working health check script",
    "docker-compose.yml": "# Complete service definition",
    "README.md": "# Updated documentation"
}}

**BRIDGE IMPLEMENTATION REQUIREMENTS:**
The mcp_bridge.py must:
- Use subprocess.Popen to run the actual MCP server CLI command
- Implement proper JSON-RPC over stdin/stdout communication
- Handle MCP protocol initialization sequence
- Provide HTTP endpoints that translate to MCP tool calls
- Include comprehensive error handling and logging
- Bind to 0.0.0.0:8080 for container access

Fix the specific error and generate a complete, working deployment package as JSON.
"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,  # Increased for multiple files
        temperature=0.1,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text

    return _parse_deployment_package(message) 