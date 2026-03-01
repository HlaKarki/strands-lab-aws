import asyncio
import json
from playwright.async_api import async_playwright

# Data we are interested in
data_we_need = [
    "content.matchFacts.playerOfTheMatch", "content.matchFacts.infoBox",
    "content.matchFacts.postReview", "content.matchFacts.preReview",
    "content.matchFacts.topPlayer", "content.stats.Periods.All.stats",
]

data_for_later =[
    "content.playerStats", "content.shotmap", "content.lineup"
    "content.h2h", "content.momentum",
]

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        page = await context.new_page()

        # Capture API responses
        api_response = None
        async def handle_response(response):
            nonlocal api_response
            if 'matchDetails?matchId=' in response.url:
                print(f"Intercepted: {response.url}")
                try:
                    data = await response.json()
                    api_response = data
                except:
                    print(f"Status: {response.status}")

        page.on('response', handle_response)

        # Visit a match page instead of API directly
        print("Visiting match page...")
        match_url = "https://www.fotmob.com/match/4813652"
        await page.goto(match_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)  # Wait for API calls

        if api_response:
            print("\n=== GOT API RESPONSE ===")
            cleaned = {}
            for path in data_we_need:
                keys = path.split('.')
                value = api_response
                for key in keys:
                    value = value.get(key) if isinstance(value, dict) else None
                    if value is None:
                        break
                if value is not None:
                    cleaned[path] = value

            print(json.dumps(cleaned, indent=2))
        else:
            print("\n=== NO API RESPONSE CAPTURED ===")

        # await browser.close()

if __name__ == "__main__":
    asyncio.run(test())