---
name: Advice Slip
description: Fetches a random piece of advice. The user query would be something like "give me some advice".
documentation_summary: Provides a random piece of life advice.
base_url: https://api.adviceslip.com/advice
examples:
  - user_query: "I need some advice"
    code: |
      import httpx, json
      resp = httpx.get("https://api.adviceslip.com/advice", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 