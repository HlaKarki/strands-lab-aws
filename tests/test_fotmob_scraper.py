import asyncio

from services.fotmob import FotmobClient

async def test_get_match_details():
    fb_client = FotmobClient()
    result = await fb_client.get_match_details(4813652)
    assert result is not None
    assert 'general' not in result
    assert 'content.matchFacts.preReview'
    print("Match details fetched and key data extracted successfully")

if __name__ == '__main__':
    asyncio.run(test_get_match_details())