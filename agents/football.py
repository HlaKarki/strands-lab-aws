import os
import logging
import asyncio
from datetime import datetime
from typing import List

import httpx
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import shell

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
        response = await client.get(f"{base_url}?date={date}&timezone=America/New_York&ccode3=USA")
        data = response.json()
        relevant_leagues = [
            league for league in data["leagues"]
            if league["primaryId"] in AVAILABLE_LEAGUES_BY_ID
        ]

        logger.info(f"Found {len(relevant_leagues)} relevant leagues:")
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
        logger.info(f"Fetching matches for date: {date}")
        result = await fetch_matches_by_date(date) # type: ignore
        if result:
            all_matches.extend(result)

    return all_matches

async def main():
    agent = Agent(
        model=BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION")),
        tools=[fetch_matches_by_date, fetch_matches_by_multiple_dates],
        callback_handler=callback_handler,
        system_prompt=f"""You are a football assistant and enthusiast.
        
        Today's date: {datetime.now().strftime('%A, %B %d, %Y')} (YYYYMMDD: {datetime.now().strftime('%Y%m%d')})
        
        When users ask about fixtures pertaining to specific dates, calculate the YYYYMMDD format yourself and pass it to 
        the tool."""
    )

    result = await agent.invoke_async("Show me January first week's fixture results")

    # Print just the text content from the assistant's response
    print(result.message["content"][0]["text"])

if __name__ == "__main__":
    asyncio.run(main())