import os
import httpx
import logging
import asyncio
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel
from scrapers.fotmob import get_match_details_from_browser
from utils import fotmob_headers, GENERAL_SYSTEM_PROMPT

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger("my_agent")

tool_use_ids = []
def callback_handler(**kwargs):
    if "current_tool_use" in kwargs:
        tool = kwargs["current_tool_use"]
        if tool["toolUseId"] not in tool_use_ids:
            logger.info(f"\n[Using tool: {tool.get('name')}]")
            tool_use_ids.append(tool["toolUseId"])


AVAILABLE_LEAGUES_BY_ID = {
    47: "Premier League",
    42: "Champions League",
    73: "Europa League",
    87: "LaLiga",
    54: "Bundesliga",
    53: "Ligue 1",
}

AVAILABLE_LEAGUES = {v: k for k, v in AVAILABLE_LEAGUES_BY_ID.items()}

@tool
async def fetch_matches_by_date(date: int):
    """
    Fetch football matches by date
    :param date: Date in YYYYMMDD format
    :return: Dictionary of matches for that specific date
    """
    base_url = "https://www.fotmob.com/api/data/matches"
    logger.info(f"Fetching matches for date: {date}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}?date={date}&timezone=America/New_York&ccode3=USA",
            headers=fotmob_headers
        )
        data = response.json()
        relevant_leagues = [
            league for league in data["leagues"]
            if league["primaryId"] in AVAILABLE_LEAGUES_BY_ID
        ]

        return relevant_leagues

@tool
async def fetch_matches_by_multiple_dates(dates: List[int]):
    """
    Fetch football matches by multiple dates.
    Use this when the user asks for matches across multiple days (e.g., "first week of January").

    :param dates: List of dates in YYYYMMDD format (e.g., [20260101, 20260102, 20260103])
    :return: List of matches grouped by date
    """
    logger.info(f"Fetching matches for the dates: {dates}")
    all_matches = []
    for date in dates:
        result = await fetch_matches_by_date(date) # type: ignore
        if result:
            all_matches.extend(result)

    return all_matches

@tool
async def get_match_details(match_id: int) -> Dict:
    """
    Fetch comprehensive match details using match ID. Returns highly detailed match information.

    Use this tool when users want:
    - Goal scorers and assist providers
    - Cards/disciplinary information
    - Expected goals (xG) statistics
    - Detailed event information
    - Match timing and status updates

    :param match_id: Unique integer ID of the match to fetch details for
    :return: Dictionary with 'general' and 'header' objects containing comprehensive
             match details including events, statistics, and team information
    """
    # logger.info(f"Fetching match details for match_id: {match_id}")
    return await get_match_details_from_browser(match_id)

@tool
async def get_league_table(league_name: str):
    f"""
    Fetch the current league standings/table for a specific competition.

    Returns comprehensive league table information including:
    - Team rankings (position, points, games played)
    - Form guide (recent results)
    - Goals for/against and goal difference
    - Win/draw/loss records
    - Qualification status (Champions League, Europa League, relegation zones)

    Use this tool when users want:
    - Current league standings ("show me the Premier League table")
    - Team positions ("where is Arsenal in the table?")
    - Points and form ("how many points does Liverpool have?")
    - Top of the table or relegation battles
    - Goal difference and scoring stats

    Available leagues: {list(AVAILABLE_LEAGUES_BY_ID.values())}

    :param league_name: Name of the league (must exactly match one from available leagues list)
    :return: Array of team objects with position, points, form, goals, and qualification info
    """
    league_id = AVAILABLE_LEAGUES[league_name]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://www.fotmob.com/api/data/tltable?leagueId={league_id}",
            headers=fotmob_headers
        )
        datas = response.json()
        for data in datas:
            table_all = (
                data.get("data", {})
                .get("table", {})
                .get("all")
            )
            if table_all:
                return table_all

        return None

@tool
async def get_league_statistics(league_name: str):
    """
    Fetch league statistics using league ID
    :param league_name:
    :return:
    """

def get_football_agent():
    return Agent(
        model=BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION")),
        tools=[fetch_matches_by_date, fetch_matches_by_multiple_dates, get_match_details, get_league_table],
        callback_handler=callback_handler,
        system_prompt=f"""You are a football assistant and enthusiast.

            Today's date: {datetime.now().strftime('%A, %B %d, %Y')} (YYYYMMDD: {datetime.now().strftime('%Y%m%d')})

            When users ask about fixtures pertaining to specific dates, calculate the YYYYMMDD format yourself and pass it to 
            the tool.
            
            {GENERAL_SYSTEM_PROMPT}
            """
    )

async def main():
    agent = get_football_agent()

    result = await agent.invoke_async("Show me January first week's fixture results")

    print(result.message["content"][0]["text"])

if __name__ == "__main__":
    asyncio.run(main())