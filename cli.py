import random

COMMANDS = {
    "/learn": { "description": "System design interview prep coach" },
    "/football": { "description": "Football enthusiast and analyst agent" }
}

def make_user_id() -> str:
    adjectives = ["blue", "fast", "silent", "brave"]
    nouns = ["tiger", "eagle", "wolf", "panda"]

    return f"{random.choice(adjectives)}-{random.choice(nouns)}-{random.randint(100, 999)}"

def main():
    user_id = make_user_id()
    print(f"\n Commands: {', '.join(COMMANDS.keys())}")
    print(f"Type '/exit' to quit\n")
    print(f"User ID: {user_id}")

    while True:
        try:
            user_input = input("> ").strip()

            if not user_input:
                continue

            if user_input == "/exit":
                # save conversation/progress
                break

            parts = user_input.split(maxsplit=1)
            command = parts[0]
            message = parts[1] if len(parts) > 1 else ""

            # chat
            if not command.startswith("/"):
                print(f"This is just a chat!")
                continue

            # command chat
            if command not in COMMANDS:
                print(f"Unknown command. Available commands: {', '.join(COMMANDS.keys())}")
                continue

            # get orchestrator instance?
            print(f"Command: {command}")

        except KeyboardInterrupt:
            # save conversation/progress
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()