---
name: CoinGecko
description: Fetches the current price of a cryptocurrency in USD. You need to extract the name of the cryptocurrency (e.g., 'bitcoin', 'ethereum') from the user's query.
documentation_summary: Gets the real-time price of various cryptocurrencies against USD.
base_url: https://api.coingecko.com/api/v3/simple/price
examples:
  - user_query: "what is the price of ethereum?"
    code: |
      import httpx, json
      crypto_id = "ethereum"
      resp = httpx.get(f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd", timeout=5)
      print(json.dumps(resp.json(), indent=2))
  - user_query: "show me the bitcoin price"
    code: |
      import httpx, json
      crypto_id = "bitcoin"
      resp = httpx.get(f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 