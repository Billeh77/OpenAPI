---
name: Cat Facts
description: Provides a random fact about cats. The user query would be something like "tell me a cat fact".
documentation_summary: Returns a random, brief fact about cats.
base_url: https://catfact.ninja/fact
examples:
  - user_query: "give me a fun cat fact"
    code: |
      import httpx, json
      resp = httpx.get("https://catfact.ninja/fact", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 