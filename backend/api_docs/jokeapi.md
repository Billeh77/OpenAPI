---
name: JokeAPI
description: Fetches a random joke. It can be a single-part joke or a two-part joke (setup and delivery). The user query would be something like "tell me a joke".
documentation_summary: Delivers random jokes from various categories, can be single or two-part.
base_url: https://v2.jokeapi.dev/joke/Any
examples:
  - user_query: "tell me a random joke"
    code: |
      import httpx, json
      resp = httpx.get("https://v2.jokeapi.dev/joke/Any", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 