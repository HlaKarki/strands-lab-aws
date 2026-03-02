import asyncio

from services.fotmob import FotmobClient

async def fetch_matches_by_date():
    fb_client = FotmobClient()
    result = await fb_client.fetch_fixtures_by_date(20260301)
    print(f"Got {len(result)} leagues")
    assert len(result) > 0

if __name__ == "__main__":
    asyncio.run(fetch_matches_by_date())
