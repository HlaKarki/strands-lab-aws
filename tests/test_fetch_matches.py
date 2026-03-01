import asyncio
import json
from agents.football import fetch_matches_by_date

if __name__ == "__main__":
    result = asyncio.run(fetch_matches_by_date(20260301))
    print(f"Got {len(result)} leagues")
    if result and len(result) > 0:
        league = result[0]
        print(f"\nLeague: {league.get('name', 'Unknown')}")
        if 'matches' in league and len(league['matches']) > 0:
            match = league['matches'][0]
            print(f"\nFirst match keys: {list(match.keys())}")
            print(f"\nFirst match data:")
            print(json.dumps(match, indent=2))