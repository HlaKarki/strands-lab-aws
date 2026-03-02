import asyncio
import json

from services.fotmob import FotmobClient

async def test_get_match_details():
    fb_client = FotmobClient()
    result = await fb_client.get_match_details(4813652)
    print(result)
    assert result is not None
    assert 'general' not in result
    assert 'content.matchFacts.preReview'
    print("Match details fetched and key data extracted successfully")

async def predict_fixture():
    fb_client = FotmobClient()
    result = await fb_client.get_fixture_preview(4837368)
    # print(json.dumps(result, indent=2))
    print(result)
    assert result is not None

if __name__ == '__main__':
    # asyncio.run(test_get_match_details())
    asyncio.run(predict_fixture())