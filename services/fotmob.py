import os
import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel
from scrapers.browser import intercept_api_response

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger("fotmob_client")

class FotmobClient:
    def __init__(self):
        self.base_url = "https://www.fotmob.com/api"
        self.client = httpx.AsyncClient()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.fotmob.com/",
            "Origin": "https://www.fotmob.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        self.league_ids = {
            47: "Premier League",
            42: "Champions League",
            73: "Europa League",
            87: "LaLiga",
            54: "Bundesliga",
            53: "Ligue 1",
        }
        self.league_names = {v: k for k, v in self.league_ids.items()}
        self.tool_use_ids = []
        self.output_prompt = """Output Formatting:
        - This is a CLI terminal application. DO NOT use markdown formatting.
        - NO bold (**text**), NO headers (##), NO italics, NO markdown syntax.
        - Use plain text with clear structure:
          * Section headers in UPPERCASE or with simple prefixes like "==="
          * Use indentation (2-4 spaces) for hierarchy
          * Use simple ASCII separators: ---, ===, •, -, etc.
          * Use line breaks for readability

        Example good CLI output:

        BRUNO FERNANDES STATS
        Match Rating: 9.2 (Man of the Match)

        Goals: 1 (57' - Penalty)
        Assists: 1
        Minutes: 90

        Attacking:
          - xG: 0.86
          - Shots: 3 on target, 1 off target
          - Chances created: 6

        Passing:
          - Accurate passes: 49/67 (73%)
          - Crosses: 3/6 (50%)
        """

    def callback_handler(self, **kwargs):
        if "current_tool_use" in kwargs:
            tool_object = kwargs["current_tool_use"]
            if tool_object["toolUseId"] not in self.tool_use_ids:
                logger.info(f"\n[Using tool: {tool_object.get('name')}]")
                self.tool_use_ids.append(tool_object["toolUseId"])

    @staticmethod
    def extract_key_data(match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract only the important fields from match data.

        :param match_data: Full match details response
        :return: Cleaned data with only needed fields
        """
        paths = [
            "header", "content.matchFacts.playerOfTheMatch", "content.matchFacts.infoBox",
            "content.matchFacts.postReview", "content.matchFacts.preReview",
            "content.matchFacts.topPlayer", "content.stats.Periods.All.stats",
        ]
        data_for_later = [
            "content.playerStats", "content.shotmap", "content.lineup", "content.h2h", "content.momentum",
        ]
        cleaned = {}
        for path in paths:
            keys = path.split(".")
            value = match_data
            for key in keys:
                value = value.get(key) if isinstance(value, dict) else None
                if value is None:
                    break
            if value is not None:
                cleaned[path] = value

        return cleaned

    @tool
    async def fetch_matches_by_date(self, date: int):
        """
        Fetch football matches by date
        :param date: Date in YYYYMMDD format
        :return: Dictionary of matches for that specific date
        """
        base_url = "https://www.fotmob.com/api/data/matches"
        logger.info(f"Fetching matches for date: {date}")

        response = await self.client.get(
            f"{base_url}?date={date}&timezone=America/New_York&ccode3=USA",
            headers=self.headers
        )
        data = response.json()

        relevant_leagues = [
            league for league in data["leagues"]
            if league["primaryId"] in self.league_ids
        ]
        return relevant_leagues

    @tool
    async def fetch_matches_by_multiple_dates(self, dates: List[int]):
        """
        Fetch football matches by multiple dates.
        Use this when the user asks for matches across multiple days (e.g., "first week of January").

        :param dates: List of dates in YYYYMMDD format (e.g., [20260101, 20260102, 20260103])
        :return: List of matches grouped by date
        """
        logger.info(f"Fetching matches for the dates: {dates}")
        all_matches = []
        for date in dates:
            result = await self.fetch_matches_by_date(date)  # type: ignore
            if result:
                all_matches.extend(result)

        return all_matches

    @tool
    async def get_league_table(self, league_name: str):
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

        Available leagues: {list(self.league_ids.values())}

        :param league_name: Name of the league (must exactly match one from available leagues list)
        :return: Array of team objects with position, points, form, goals, and qualification info
        """
        league_id = self.league_names[league_name]

        response = await self.client.get(
            f"https://www.fotmob.com/api/data/tltable?leagueId={league_id}",
            headers=self.headers
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
    async def get_league_statistics(self, league_name: str):
        """
        Fetch league statistics using league ID
        :param league_name:
        :return:
        """
        league_id = self.league_names[league_name]
        response = await self.client.get(f"https://www.fotmob.com/api/data/leagues?id={league_id}&ccode3=USA_MD")
        data = response.json()
        cleaned = {
            "seasons": data.get("allAvailableSeasons"),
            "overview": data.get("overview"),
            "stats": data.get("stats"),
        }
        return cleaned

    @tool
    async def get_match_details(self, match_id: int) -> Dict:
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
        logger.info(f"Fetching match details for match_id: {match_id}")
        match_url = f"https://www.fotmob.com/match/{match_id}"

        def response_filter(url: str) -> bool:
            return f"matchDetails?matchId={match_id}" in url

        result = await intercept_api_response(
            url=match_url,
            response_filter=response_filter,
            headless=True,
            timeout_ms=10000
        )

        if not result:
            raise Exception(f"Failed to fetch match details for match_id: {match_id}")

        return self.extract_key_data(result)

    def get_football_agent(self):
        return Agent(
            model=BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION")),
            tools=[
                self.fetch_matches_by_date,
                self.fetch_matches_by_multiple_dates,
                self.get_match_details,
                self.get_league_table
            ],
            callback_handler=self.callback_handler,
            system_prompt=f"""You are a football assistant and enthusiast.

                Today's date: {datetime.now().strftime('%A, %B %d, %Y')} (YYYYMMDD: {datetime.now().strftime('%Y%m%d')})

                When users ask about fixtures pertaining to specific dates, calculate the YYYYMMDD format yourself and pass it to 
                the tool.

                {self.output_prompt}
                """
        )

