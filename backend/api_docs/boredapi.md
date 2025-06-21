---
name: BoredAPI
description: Suggests a random activity to do when bored. The user query would be something like "I'm bored" or "suggest an activity".
documentation_summary: Suggests a random activity when a user is bored.
base_url: https://www.boredapi.com/api/activity
examples:
  - user_query: "I'm bored, what can I do?"
    code: |
      import httpx, json
      resp = httpx.get("https://www.boredapi.com/api/activity", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 