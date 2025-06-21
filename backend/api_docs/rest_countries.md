---
name: REST Countries
description: Provides detailed information about a specific country. You need to extract a country name from the user's query.
documentation_summary: Retrieves detailed geopolitical data about a country by its name.
base_url: https://restcountries.com/v3.1/name/
examples:
  - user_query: "tell me about Germany"
    code: |
      import httpx, json
      # User query was "tell me about Germany"
      country_name = "Germany"
      resp = httpx.get(f"https://restcountries.com/v3.1/name/{country_name}", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 