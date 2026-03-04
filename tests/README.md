## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_fotmob_tools.py

# Run specific test
uv run pytest tests/test_fotmob_tools.py::test_search_fotmob_player
```
