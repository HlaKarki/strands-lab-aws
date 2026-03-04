import asyncio
import json
from playwright.async_api import async_playwright

async def test():
    player_id = 422685
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
            print(f"Response: {response.url}")
            if f'playerData?id={player_id}' in response.url:
                print(f"✓ Intercepted: {response.url}")
                try:
                    data = await response.json()
                    api_response = data
                    print(f"✓ JSON parsed successfully")
                except Exception as e:
                    print(f"✗ Failed to parse JSON: {e}")
                    print(f"Status: {response.status}")

        page.on('response', handle_response)

        # Visit player page
        print(f"Visiting player page {player_id}...")
        player_url = f"https://www.fotmob.com/players/{player_id}/"
        await page.goto(player_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)  # Wait for page to load

        # Try to extract data from window.__NEXT_DATA__
        print("\n=== Trying window.__NEXT_DATA__ ===")
        next_data = await page.evaluate("() => window.__NEXT_DATA__")

        player_data = None
        if next_data:
            print(f"✓ Found __NEXT_DATA__")
            print(f"Top-level keys: {list(next_data.keys())}")

            # Look for player data in props
            if 'props' in next_data:
                print(f"Props keys: {list(next_data['props'].keys())}")
                if 'pageProps' in next_data['props']:
                    print(f"PageProps keys: {list(next_data['props']['pageProps'].keys())}")
                    if 'data' in next_data['props']['pageProps']:
                        player_data = next_data['props']['pageProps']['data']
                        print(f"\n✓ Found player data!")
                        print(f"Player data keys: {list(player_data.keys())}")
        else:
            print("✗ No __NEXT_DATA__ found")

        if api_response:
            print("\n=== GOT API RESPONSE (from intercept) ===")
            print(f"Keys: {list(api_response.keys())}")
        else:
            print("\n=== NO API RESPONSE CAPTURED ===")

        # Keep browser open - wait for user input before closing (uncomment to debug)
        # input("Press Enter to close browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test())