from collections.abc import Callable
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

async def extract_nextjs_data(
    url: str,
    data_path: str = "props.pageProps.data",
    headless: bool = True,
    debug: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Extract data from Next.js __NEXT_DATA__ object

    :param url: URL to visit
    :param data_path: Dot-notation path to data in __NEXT_DATA__ (e.g., "props.pageProps.data")
    :param headless: Run browser in headless mode
    :param debug: Print debug information
    :return: Extracted data or None
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        page = await context.new_page()

        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)  # Wait for page to load

        # Extract __NEXT_DATA__
        next_data = await page.evaluate("() => window.__NEXT_DATA__")

        await browser.close()

        if not next_data:
            if debug:
                print("No __NEXT_DATA__ found")
            return None

        # Navigate to the desired data using the path
        data = next_data
        for key in data_path.split('.'):
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                if debug:
                    print(f"Path '{data_path}' not found in __NEXT_DATA__")
                return None

        return data

async def intercept_api_response(
    url: str,
    response_filter: Callable[[str], bool],
    headless: bool = True,
    timeout_ms: int = 10000,
    debug: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Generic function to visit a page and intercept API reponse

    :param url: URL to visit
    :param response_filter: Function that returns True if response should be returned
    :param headless: Run browser in headless mode
    :param timeout_ms: Max wait time for response
    :param debug: Print all response URLs for debugging
    :return: Intercepted JSON response or None
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        page = await context.new_page()

        api_response = None
        async def handle_response(response):
            nonlocal api_response
            if debug:
                print(f"Response URL: {response.url}")
            if response_filter(response.url):
                try:
                    api_response = await response.json()
                except Exception as e:
                    if debug:
                        print(f"Failed to parse JSON from {response.url}: {e}")
        page.on('response', handle_response)
        await page.goto(url, wait_until="domcontentloaded")

        # Wait for response
        for _ in range(timeout_ms // 200):
            if api_response:
                break
            await page.wait_for_timeout(200)

        await browser.close()
        return api_response