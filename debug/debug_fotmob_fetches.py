import asyncio

from agents.football import get_league_table


async def main():
    result = await get_league_table("Premier League")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())