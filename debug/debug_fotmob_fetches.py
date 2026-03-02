import asyncio

from services.fotmob import FotmobClient

async def main():
    fb_client = FotmobClient()
    # result = await fb_client.get_league_table("Premier League")
    # result = await fb_client.get_league_statistics("Premier League")

    print(fb_client.teams_data_path)
    await fb_client.sync_team_ids()

if __name__ == "__main__":
    asyncio.run(main())