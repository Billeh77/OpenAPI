---
name: Nager.Date Public Holidays
description: Fetches the public holidays for a given year and country code. You need to extract a year (e.g., 2024) and a two-letter country code (e.g., US, DE, FR) from the user's query.
documentation_summary: Lists public holidays for a given country and year.
base_url: https://date.nager.at/api/v3/PublicHolidays
examples:
  - user_query: "what are the holidays in Canada for 2025?"
    code: |
      import httpx, json
      # User query was "what are the holidays in Canada for 2025?"
      year = "2025"
      country_code = "CA"
      resp = httpx.get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}", timeout=10)
      print(json.dumps(resp.json(), indent=2))
  - user_query: "holidays in US this year"
    code: |
      import datetime
      year = str(datetime.datetime.now().year)
      country_code = "US"
      resp = httpx.get(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}", timeout=10)
      print(json.dumps(resp.json(), indent=2))
--- 