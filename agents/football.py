import asyncio
from dotenv import load_dotenv

from services.fotmob import FotmobClient

load_dotenv()

async def main():
    fb_client = FotmobClient()
    agent = fb_client.get_football_agent()

    result = await agent.invoke_async("Show me this weekend's premier league results")

    print(result.message["content"][0]["text"])

if __name__ == "__main__":
    asyncio.run(main())