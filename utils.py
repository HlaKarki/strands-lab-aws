import random


def make_user_id() -> str:
    adjectives = ["blue", "fast", "silent", "brave"]
    nouns = ["tiger", "eagle", "wolf", "panda"]

    return f"{random.choice(adjectives)}-{random.choice(nouns)}-{random.randint(100, 999)}"

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