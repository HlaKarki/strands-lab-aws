import logging
from typing import Dict, Any

from scrapers.browser import intercept_api_response

logger = logging.getLogger(__name__)

async def get_match_details_from_browser(match_id: int) -> Dict[str, Any]:
    """
    Fetch comprehensive match details from Fotmob.

    :param match_id: Unique match ID
    :return: Match details dictionary
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

    return extract_key_data(result)

def extract_key_data(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract only the important fields from match data.

    :param match_data: Full match details response
    :return: Cleaned data with only needed fields
    """
    paths = [
        "content.matchFacts.playerOfTheMatch", "content.matchFacts.infoBox",
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