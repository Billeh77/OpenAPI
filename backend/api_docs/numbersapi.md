---
name: Numbers API
description: Fetches a trivia fact about a specific number. You need to extract a number from the user's query. It can handle random numbers by using 'random' in the URL.
documentation_summary: Gives a trivia fact about a specific or random number.
base_url: http://numbersapi.com/
examples:
  - user_query: "what is a fun fact about the number 27?"
    code: |
      import httpx, json
      # User query was "what is a fun fact about the number 27?"
      number = "27"
      resp = httpx.get(f"http://numbersapi.com/{number}/trivia?json", timeout=5)
      print(json.dumps(resp.json(), indent=2))
  - user_query: "tell me a fact about a random number"
    code: |
      resp = httpx.get(f"http://numbersapi.com/random/trivia?json", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 