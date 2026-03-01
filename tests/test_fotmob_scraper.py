import asyncio

from scrapers.fotmob import get_match_details_from_browser

async def test_get_match_details():
    result = await get_match_details_from_browser(4813652)
    assert result is not None
    assert 'general' not in result
    assert 'content.matchFacts.preReview'
    print("Match details fetched and key data extracted successfully")

if __name__ == '__main__':
    asyncio.run(test_get_match_details())