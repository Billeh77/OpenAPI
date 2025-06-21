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
You are an expert Python programmer. Your primary task is to write a single, self-contained Python script based on a user's query and provided API documentation.

**CRITICAL RULES:**
1.  **OUTPUT ONLY PYTHON CODE.** Your final response must contain *only* the Python code, and nothing else.
2.  Do **NOT** include the `<thinking>` block, markdown fences (```python), or any other explanatory text in your final response. The response should be immediately executable as a Python script.
3.  The script must use the `httpx` and `json` libraries.
4.  The script's final output to standard output **MUST** be a single, well-formed JSON object.
5.  Implement comprehensive error handling using a `try...except` block to catch potential exceptions and print the error message as a JSON object (e.g., `print(json.dumps({"error": "message"}))`).
6.  Use the provided API documentation (in JSON format) to understand how to call the API, what parameters are needed, and how to construct the URL. Extract any necessary parameters from the user's query.

First, think step-by-step about the user's request and the provided documentation inside `<thinking>` tags. Then, provide the complete, runnable Python script as your final answer.
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

def generate_code(user_query: str, retrieved_docs: list[dict]) -> str:
    """Generates Python code based on the user query and retrieved structured API docs."""
    if not client:
        raise ValueError("Anthropic client is not initialized. Please set the CLAUDE_API_KEY.")

    docs_json_str = json.dumps(retrieved_docs, indent=2)
    
    prompt = f"""<user_query>
{user_query}
</user_query>
<api_documentation>
{docs_json_str}
</api_documentation>
"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=2048,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text
    
    return _extract_code(message)


def generate_code_with_retry(old_code: str, error: str, user_query: str, retrieved_docs: list[dict]) -> str:
    """Attempts to fix broken code given the error it produced and the original context."""
    if not client:
        raise ValueError("Anthropic client is not initialized. Please set the CLAUDE_API_KEY.")

    print(f"--- Code failed. Retrying with error: {error} ---")
    
    docs_json_str = json.dumps(retrieved_docs, indent=2)
    
    prompt = f"""
The previous attempt to write a Python script failed. Here is all the context to fix it.

**Original User Query:**
<user_query>
{user_query}
</user_query>

**API Documentation Provided:**
<api_documentation>
{docs_json_str}
</api_documentation>

**The Code That Failed:**
<original_code>
{old_code}
</original_code>

**The Error It Produced:**
<error_traceback>
{error}
</error_traceback>

Please analyze the original query, the documentation, the failed code, and the error. Provide the fully corrected, complete Python script.
Think step-by-step about what went wrong and how to fix it inside the <thinking> tags, then provide ONLY the corrected Python code.
"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=2048,
        temperature=0.1,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ).content[0].text

    return _extract_code(message) 