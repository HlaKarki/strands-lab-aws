import os
import httpx
import logging
from datetime import datetime
from typing import List, Any
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
          
        
        Example; for league table, present in neat format as such:
        POS  TEAM                          P   W   D   L    GF-GA     GD   PTS
        ---  ----------------------------- --- --- --- ---  --------  ---- ----
          1  Barcelona                     26  21   1   4   71-26     +45   64
          2  Real Madrid                   25  19   3   3   54-21     +33   60
          3  Atletico Madrid               26  15   6   5   43-23     +20   51
          4  Villarreal                    26  16   3   7   48-31     +17   51
          5  Real Betis                    26  11  10   5   42-32     +10   43
          6  Celta Vigo                    26  10  10   6   36-28      +8   40
        -----------------------------------------------------------------------
          7  Espanyol                      26  10   6  10   33-39      -6   36
          8  Real Sociedad                 26   9   8   9   38-38       0   35
          9  Athletic Club                 26  10   5  11   30-36      -6   35
         10  Osasuna                       26   9   6  11   30-30       0   33
         11  Sevilla                       26   8   6  12   34-41      -7   30
         12  Girona                        26   7   9  10   27-42     -15   30
         13  Valencia                      26   7   8  11   27-39     -12   29
         14  Getafe                        25   8   5  12   20-29      -9   29
         15  Rayo Vallecano                25   6   9  10   23-32      -9   27
         16  Deportivo Alaves              26   7   6  13   23-34     -11   27
         17  Elche                         26   5  11  10   34-39      -5   26
        -----------------------------------------------------------------------
         18  Mallorca                      26   6   6  14   29-42     -13   24
         19  Levante                       26   5   6  15   28-44     -16   21
         20  Real Oviedo                   25   3   8  14   16-40     -24   17
        """

    def callback_handler(self, **kwargs):
        if "current_tool_use" in kwargs:
            tool_object = kwargs["current_tool_use"]
            if tool_object["toolUseId"] not in self.tool_use_ids:
                logger.info(f"\n[Using tool: {tool_object.get('name')}]")
                self.tool_use_ids.append(tool_object["toolUseId"])

    @staticmethod
    def parse_league_overview(league_overview: dict) -> dict[str, dict]:
        return {
            "topPlayers": league_overview.get("topPlayers", {})
        }

    @staticmethod
    def parse_league_stats(league_stats: dict) -> dict[str, List]:
        return {
            "players": league_stats.get("players", []),
            "teams": league_stats.get("teams", []),
        }

    @staticmethod
    def extract_key_data(match_data: dict[str, Any]) -> dict[str, Any]:
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

    @staticmethod
    def parse_fixture_insights(match_details: dict[str, Any]) -> List:
        general = match_details.get("general", {})
        home = general.get("homeTeam", {})
        away = general.get("awayTeam", {})
        team_ids = {}

        if home_id := home.get("id"):
            team_ids[home_id] = home.get("name", "home")

        if away_id := away.get("id"):
            team_ids[away_id] = away.get("name", "away")

        facts = []
        if insights := (
            match_details.get("content", {})
                .get("matchFacts", {})
                .get("insights")
        ):
            for insight in insights:
                if not (fact := insight.get("text")) or insight.get("type") != "team":
                    continue

                team_id = insight.get("teamId")
                if team_id and team_id in team_ids:
                    facts.append(f"{team_ids[team_id]} {fact}")
                    continue

                facts.append(fact)

        if facts_from_poll := (
            match_details.get("content", {})
                .get("matchFacts", {})
                .get("poll")
                .get("oddspoll")
                .get("Facts")
        ):
            for fact_object in facts_from_poll:
                if fact := fact_object.get("defaultText"):
                    facts.append(fact)

        return facts

    @staticmethod
    def parse_fixture_content(match_details: dict[str, Any]) -> dict[str, Any]:
        content = match_details.get("content", {})
        cleaned_content = {}
        home_name = "home"
        away_name = "away"

        if lineup := content.get("lineup"):
            if home_team := lineup.get("homeTeam"):
                home_name = home_team.get("name", "home")
                cleaned_content[home_name] = {
                    "unavailable_players": home_team.get("unavailable", []),
                    "average_starter_age": home_team.get("averageStarterAge", None),
                    "total_starter_market_value": home_team.get("totalStarterMarketValue", None),
                    "formation": home_team.get("formation", None),
                }

            if away_team := lineup.get("awayTeam"):
                away_name = away_team.get("name", "away")
                cleaned_content[away_name] = {
                    "unavailable_players": away_team.get("unavailable", []),
                    "average_starter_age": away_team.get("averageStarterAge", None),
                    "total_starter_market_value": away_team.get("totalStarterMarketValue", None),
                    "formation": away_team.get("formation", None),
                }

            if team_form := content.get("matchFacts").get("teamForm"):
                cleaned_content[home_name]["form"] = team_form[0]
                cleaned_content[away_name]["form"] = team_form[1]

            if weather := content.get("weather"):
                cleaned_content["weather"] = weather

            if head_to_head := content.get("h2h"):
                cleaned_content["head_to_head"] = { "summary": {}, "matches": {} }
                cleaned_content["head_to_head"]["summary"] = {
                    f"{home_name} Wins": head_to_head["summary"][0],
                    f"{away_name} Wins": head_to_head["summary"][2],
                    "Draws": head_to_head["summary"][1],
                }
                cleaned_content["head_to_head"]["matches"] = head_to_head["matches"]

        return cleaned_content

    @tool
    async def fetch_fixtures_by_date(self, date: int):
        """
        Fetch football matches by date
        :param date: Date in YYYYMMDD format
        :return: dictionary of matches for that specific date
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
    async def fetch_fixtures_by_multiple_dates(self, dates: List[int]):
        """
        Fetch football matches by multiple dates.
        Use this when the user asks for matches across multiple days (e.g., "first week of January").

        :param dates: List of dates in YYYYMMDD format (e.g., [20260101, 20260102, 20260103])
        :return: List of matches grouped by date
        """
        logger.info(f"Fetching matches for the dates: {dates}")
        all_matches = []
        for date in dates:
            result = await self.fetch_fixtures_by_date(date)  # type: ignore
            if result:
                all_matches.extend(result)

        return all_matches

    @tool
    async def get_completed_fixture_details(self, match_id: int) -> dict:
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

        NOTE: For "best/rated teams" by performance metrics, use get_league_statistics instead.

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
        f"""
        Fetch detailed player and team statistics for a specific league.

        Returns comprehensive statistical data including:
        - Top performing players across various categories
        - Player statistics (goals, assists, appearances, etc.)
        - Team statistics: FotMob ratings, goals per match, possession, clean sheets, and 20+ other metrics

        Use this tool when users want:
        - Top scorers or assist leaders ("who's leading the Golden Boot?")
        - Player performance statistics ("best players in the Premier League")
        - **Team ratings or best performing teams** ("top rated teams", "best teams in the league")
        - Team statistical rankings (possession, goals per match, clean sheets, etc.)
        - League-wide statistical leaders

        NOTE: Use this for "best/rated teams" queries. Use get_league_table for standings/table position.

        Available leagues: {list(self.league_ids.values())}

        :param league_name: Name of the league (must exactly match one from available leagues list)
        :return: Dictionary with 'overview' (topPlayers) and 'stats' (players/teams arrays)
        """
        league_id = self.league_names[league_name]
        response = await self.client.get(f"https://www.fotmob.com/api/data/leagues?id={league_id}&ccode3=USA_MD")
        data = response.json()
        cleaned = {
            "overview": self.parse_league_overview(data.get("overview")),
            "stats": self.parse_league_stats(data.get("stats")),
        }
        return cleaned

    @tool
    async def get_fixture_preview(self, match_id: int):
        """
        Fetch comprehensive pre-match analysis data for an upcoming or in-progress fixture.

        Returns detailed preview information to support match predictions and analysis:
        - Team form and recent results
        - Injuries and unavailable players (suspensions, fitness issues)
        - Expected formations and lineup details
        - Head-to-head history (past results between the teams)
        - Statistical insights and trends
        - Match conditions (weather, venue details)
        - Team valuations and squad age metrics
        - Match status and timing information

        Use this tool when users want:
        - Match predictions or previews ("preview the United vs Arsenal game")
        - Injury/availability updates ("who's injured for the City match?")
        - Team form analysis ("how have both teams been playing recently?")
        - Head-to-head records ("what's the h2h between Liverpool and Chelsea?")
        - Pre-match betting insights or analysis
        - Fixture information before kickoff or during the match

        NOTE: For completed match results (goals, scorers, events), use get_match_details instead.

        :param match_id: Unique integer ID of the upcoming or in-progress fixture
        :return: Dictionary with 'facts', and 'content' for comprehensive preview
        """
        logger.info(f"Fetching pre-match details for fixture: {match_id}")
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
            raise Exception(f"Failed to fetch fixture details for match_id: {match_id}")

        # Parse the detailed data
        facts = self.parse_fixture_insights(result)
        content = self.parse_fixture_content(result)

        return {
            "facts": facts,
            "content": content,
        }

    def get_football_agent(self):
        return Agent(
            model=BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION")),
            tools=[
                self.fetch_fixtures_by_date,
                self.fetch_fixtures_by_multiple_dates,
                self.get_completed_fixture_details,
                self.get_league_table,
                self.get_league_statistics,
                self.get_fixture_preview
            ],
            callback_handler=self.callback_handler,
            system_prompt=f"""You are a football assistant and enthusiast.

                Today's date: {datetime.now().strftime('%A, %B %d, %Y')} (YYYYMMDD: {datetime.now().strftime('%Y%m%d')})

                When users ask about fixtures pertaining to specific dates, calculate the YYYYMMDD format yourself and 
                pass it to the tool.
                
                IMPORTANT: When users ask about "rated teams" or "best teams", use get_league_statistics (which has FotMob ratings).
                Only use get_league_table for standings/table position queries.

                {self.output_prompt}
                """
        )

