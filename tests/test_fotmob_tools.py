"""Integration tests for core FotmobClient tools."""
import pytest

@pytest.mark.asyncio
async def test_search_fotmob_player(fotmob_client):
    """Test searching for a player returns results."""
    results = await fotmob_client.search_fotmob("Bruno Fernandes", "player")

    assert results is not None
    assert len(results) > 0
    assert results[0]["type"] == "player"
    assert "id" in results[0]
    assert "name" in results[0]


@pytest.mark.asyncio
async def test_search_fotmob_team(fotmob_client):
    """Test searching for a team returns results."""
    results = await fotmob_client.search_fotmob("Arsenal", "team")

    assert results is not None
    assert len(results) > 0
    assert results[0]["type"] == "team"
    assert "id" in results[0]
    assert "name" in results[0]


@pytest.mark.asyncio
async def test_search_fotmob_all(fotmob_client):
    """Test searching without type filter returns mixed results."""
    results = await fotmob_client.search_fotmob("Manchester United", "all")

    assert results is not None
    assert len(results) > 0


@pytest.mark.asyncio
async def test_get_player_profile(fotmob_client):
    """Test fetching player profile data."""
    # Bruno Fernandes ID: 422685
    player_id = 422685
    result = await fotmob_client.get_player_profile(player_id)

    assert result is not None
    assert "player_info" in result
    assert "position_info" in result
    assert "primary_team" in result


@pytest.mark.asyncio
async def test_get_player_stats(fotmob_client):
    """Test fetching player stats."""
    # Bruno Fernandes ID: 422685
    player_id = 422685
    result = await fotmob_client.get_player_stats(player_id)

    assert result is not None
    assert "league_stats" in result
    assert "primary_team" in result


@pytest.mark.asyncio
async def test_get_team_fixtures(fotmob_client):
    """Test fetching team fixtures."""
    # Manchester United ID: 10260
    team_id = 10260
    result = await fotmob_client.get_team_fixtures(team_id)

    assert result is not None
    assert "fixtures" in result
    assert isinstance(result["fixtures"], dict)


@pytest.mark.asyncio
async def test_get_league_table(fotmob_client):
    """Test fetching league table."""
    result = await fotmob_client.get_league_table("Premier League")

    assert result is not None
    assert isinstance(result, list)
    assert len(result) > 0

    # Check first team has expected fields
    first_team = result[0]
    assert "name" in first_team
    assert "played" in first_team
    assert "pts" in first_team