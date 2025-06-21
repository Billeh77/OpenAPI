import json, textwrap, subprocess, tempfile, sys
from pathlib import Path
from jinja2 import Template

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

# 3️⃣ Execute generated python safely in temp subprocess
def run_code(code:str) -> str:
    # We'll use a temporary file to store and execute the code
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py", encoding='utf-8') as tf:
        tf.write(code)
        temp_filename = tf.name
    
    try:
        # Execute the temporary file using the same python interpreter
        proc = subprocess.run(
            [sys.executable, temp_filename], 
            capture_output=True, 
            text=True, 
            timeout=10,
            check=False # Do not raise exception on non-zero exit codes
        )
        
        # Combine stdout and stderr
        output = proc.stdout
        if proc.stderr:
            output += f"\nSTDERR:\n{proc.stderr}"
            
        return output

    finally:
        # Clean up the temporary file
        import os
        os.unlink(temp_filename) 