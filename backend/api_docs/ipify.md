---
name: IPIFY
description: Fetches the public IP address of the machine running the code. The user query would be something like "what is my IP address?".
documentation_summary: Returns the public IP address of the client making the request.
base_url: https://api.ipify.org
examples:
  - user_query: "what's my IP?"
    code: |
      import httpx, json
      resp = httpx.get("https://api.ipify.org?format=json", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 