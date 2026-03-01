import random


def make_user_id() -> str:
    adjectives = ["blue", "fast", "silent", "brave"]
    nouns = ["tiger", "eagle", "wolf", "panda"]

    return f"{random.choice(adjectives)}-{random.choice(nouns)}-{random.randint(100, 999)}"

fotmob_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.fotmob.com/",
        "Origin": "https://www.fotmob.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "X-Mas": "eyJib2R5Ijp7InVybCI6Ii9hcGkvZGF0YS9tYXRjaERldGFpbHM/bWF0Y2hJZD00ODEzNjUyIiwiY29kZSI6MTc3MjM4NjQ0NzMyOCwiZm9vIjoicHJvZHVjdGlvbjowZWEwNGE2NzYwZWNjN2RmNGU4MzcxOTcxYzExYThjZGQ1OTEwZWM0In0sInNpZ25hdHVyZSI6Ijc0Rjc0NkJGMDcwM0Y2ODEyNTVBQkE4MzUwQjg5MTk5In0="
}

GENERAL_SYSTEM_PROMPT = """Output Formatting:
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