import json, textwrap, subprocess, tempfile, sys
from pathlib import Path
from jinja2 import Template
import llm
import rag

# 1️⃣ Very-naïve intent → API classifier (keyword match for MVP)
API_MAP = {
    "weather": "open_meteo",
    "temperature": "open_meteo",
    "country": "rest_countries",
    "bitcoin": "coingecko",
    "crypto": "coingecko",
    "joke": "jokeapi",
    "bored": "boredapi",
    "cat": "catfacts",
    "advice": "adviceslip",
    "number": "numbersapi",
    "holiday": "nagerdate",
    "ip": "ipify",
}

def pick_api(user_query:str) -> str|None:
    for k, api in API_MAP.items():
        if k in user_query.lower():
            return api
    return None

# 2️⃣ Boilerplate generator
def build_code(api_name:str, user_query:str) -> str:
    tpl_path = Path(__file__).parent / "api_templates" / f"{api_name}.py.j2"
    tpl = Template(tpl_path.read_text())
    return tpl.render(query=user_query)

MAX_RETRIES = 2

def run_code(code: str) -> str:
    """Executes a string of Python code and returns its stdout and stderr."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py", encoding='utf-8') as tf:
        tf.write(code)
        temp_filename = tf.name
    
    try:
        proc = subprocess.run(
            [sys.executable, temp_filename], 
            capture_output=True, 
            text=True, 
            timeout=15, # Increased timeout for potentially complex code
            check=False 
        )
        
        if proc.returncode != 0:
            # If there's a non-zero exit code, we treat it as an error
            return f"Error executing code:\nExit Code: {proc.returncode}\n--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}"
        
        return proc.stdout

    finally:
        import os
        os.unlink(temp_filename)

def handle_query(user_query: str) -> dict:
    """
    Handles a user query by retrieving relevant APIs, generating code,
    executing it, and retrying on failure.
    """
    print(f"\n--- Handling query: {user_query} ---")
    
    # 1. Retrieve relevant API documentation
    try:
        retrieved_docs = rag.retrieve(user_query)
        if not retrieved_docs:
            return {"error": "Could not find any relevant API documentation."}
    except Exception as e:
        print(f"Error during RAG retrieval: {e}")
        return {"error": f"Failed to retrieve API docs: {e}"}

    # 2. Generate initial code
    try:
        code = llm.generate_code(user_query, retrieved_docs)
    except Exception as e:
        print(f"Error during code generation: {e}")
        return {"error": f"Failed to generate code: {e}"}

    # 3. Execute code with retry logic
    output = ""
    for attempt in range(MAX_RETRIES + 1):
        print(f"--- Attempt {attempt + 1} ---\nGenerated Code:\n{code}\n---")
        output = run_code(code)
        
        # Check if the output indicates an error
        if "Error executing code:" not in output:
            print("--- Code executed successfully ---")
            return {"code": code, "result": output}
        
        # If it's the last attempt, return the error
        if attempt >= MAX_RETRIES:
            print("--- Max retries reached. Returning last error. ---")
            break

        # If there's an error, try to fix the code
        try:
            code = llm.generate_code_with_retry(
                old_code=code, 
                error=output, 
                user_query=user_query,
                retrieved_docs=retrieved_docs
            )
        except Exception as e:
            print(f"Error during code retry generation: {e}")
            return {"error": f"Failed to generate retry code: {e}", "code": code, "result": output}

    # After loop, return the last result (which will be an error)
    return {"code": code, "result": output} 