import asyncio

from agents.football import get_football_agent
from utils import make_user_id

COMMANDS = {
    "/football": {
        "description": "Football enthusiast and analyst agent",
        "agent": get_football_agent()
    }
}

async def main():
    user_id = make_user_id()
    print(f"\n Commands: {', '.join(COMMANDS.keys())}")
    print(f"Type '/exit' to quit\n")
    print(f"User ID: {user_id}")

    while True:
        try:
            user_input = input("> ").strip()

            if not user_input:
                continue

            if user_input in ["/exit", "/quit", "/q", ":wq", ":q"]:
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
            agent = COMMANDS[command]["agent"]
            if agent is None:
                print(f"Unknown agent for command '{command}'")

            result = await agent.invoke_async(message)
            print(f"> {result.message['content'][0]['text']}")

        except KeyboardInterrupt:
            # save conversation/progress
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())