"""Pytest configuration and shared fixtures."""
import pytest
from services.fotmob import FotmobClient


@pytest.fixture
def fotmob_client():
    """Provides a FotmobClient instance for tests."""
    return FotmobClient()


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)