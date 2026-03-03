import asyncio

from services.fotmob import FotmobClient

async def main():
    fb_client = FotmobClient()
    # result = await fb_client.get_league_table("Premier League")
    # result = await fb_client.get_league_statistics("Premier League")

    result = await fb_client.fetch_team_details(
        10260,True
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())