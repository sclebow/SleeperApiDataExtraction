import requests
import pprint

# URL from which to fetch data
url = "https://api.sleeper.com/projections/nfl/player/6794?season_type=regular&season=2021&grouping=week"

# Perform the GET request
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the response JSON
    data = response.json()
    # Process the data as needed
    pp = pprint.PrettyPrinter()
    pp.pprint(data)
else:
    print(f"Failed to fetch data: Status code {response.status_code}")