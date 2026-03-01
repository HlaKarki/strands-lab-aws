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