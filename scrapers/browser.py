from collections.abc import Callable
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

async def intercept_api_response(
    url: str,
    response_filter: Callable[[str], bool],
    headless: bool = True,
    timeout_ms: int = 10000
) -> Optional[Dict[str, Any]]:
    """
    Generic function to visit a page and intercept API reponse

    :param url: URL to visit
    :param response_filter: Function that returns True if response should be returned
    :param headless: Run browser in headless mode
    :param timeout_ms: Max wait time for response
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
            if response_filter(response.url):
                try:
                    api_response = await response.json()
                except Exception:
                    pass
        page.on('response', handle_response)
        await page.goto(url, wait_until="domcontentloaded")

        # Wait for response
        for _ in range(timeout_ms // 200):
            if api_response:
                break
            await page.wait_for_timeout(200)

        await browser.close()
        return api_response