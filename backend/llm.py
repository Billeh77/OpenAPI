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

# A more explicit and forceful system prompt to guide the LLM's output.
SYSTEM_PROMPT = """
You are an expert DevOps engineer who writes flawless, production-quality Dockerfiles. Your sole purpose is to containerize a Model Context Protocol (MCP) server based on its documentation.

**CRITICAL INSTRUCTIONS:**
1.  **OUTPUT ONLY THE DOCKERFILE CONTENT.** Your entire response must be the raw, valid text of a Dockerfile. Do NOT include any other text, markdown fences (```dockerfile), or explanations.
2.  **START FROM A SUITABLE BASE IMAGE.** Use a specific, slim base image (e.g., `python:3.10-slim-bookworm` or `node:18-slim`).
3.  **INSTALL SYSTEM DEPENDENCIES.** Use `apt-get` to install necessary tools like `git`.
4.  **CLONE THE REPOSITORY.** Use `git clone` with the provided `repository_url`.
5.  **INSTALL APPLICATION DEPENDENCIES.** Use the correct package manager (`pip` or `npm`).
6.  **EXPOSE PORT 8080.** All MCP servers should be configured to run on port 8080 inside the container.
7.  **SET THE `CMD`.** The final command should start the MCP server, typically with flags to listen on `0.0.0.0:8080`.

First, think step-by-step inside `<thinking>` tags about the required layers. Then, provide the complete, runnable Dockerfile as your final answer.
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

def generate_dockerfile(user_query: str, retrieved_docs: list[dict]) -> str:
    """Generates Dockerfile based on the user query and retrieved MCP server docs."""
    if not client:
        raise ValueError("Anthropic client is not initialized. Please set the CLAUDE_API_KEY.")

    docs_json_str = json.dumps(retrieved_docs, indent=2)
    
    prompt = f"""
    Generate a Dockerfile to deploy the requested MCP server.
    User's Request: {user_query}
    MCP Server Documentation:
{docs_json_str}
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=2048,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text
    
    return _extract_code(message)


def generate_dockerfile_with_retry(old_dockerfile: str, error: str, user_query: str, retrieved_docs: list[dict]) -> str:
    """Attempts to fix broken Dockerfile given the error it produced and the original context."""
    if not client:
        raise ValueError("Anthropic client is not initialized. Please set the CLAUDE_API_KEY.")

    print(f"--- Dockerfile failed. Retrying with error: {error} ---")
    
    docs_json_str = json.dumps(retrieved_docs, indent=2)
    
    prompt = f"""
The previous Dockerfile build failed. Analyze the error and fix the Dockerfile.
Original Request: {user_query}
Server Documentation:
{docs_json_str}
Failed Dockerfile:
{old_dockerfile}
Build Error:
{error}
Provide ONLY the corrected, complete Dockerfile text.
"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=2048,
        temperature=0.1,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text

    return _extract_code(message) 