---
name: Open-Meteo
description: Fetches the current weather for a given latitude and longitude. The user can provide coordinates like '40.7, -74' or a city name. You must find the coordinates for a city name if provided.
documentation_summary: Provides current weather data using geographical coordinates.
base_url: https://api.open-meteo.com/v1/forecast
examples:
  - user_query: "what is the weather in Paris?"
    code: |
      import httpx, json
      # Approximate coordinates for Paris
      lat, lon = 48.8566, 2.3522
      resp = httpx.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=5)
      print(json.dumps(resp.json(), indent=2))
  - user_query: "weather in 52.5, 13.4"
    code: |
      lat, lon = 52.5, 13.4
      resp = httpx.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true", timeout=5)
      print(json.dumps(resp.json(), indent=2))
--- 