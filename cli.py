import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from agents.football import get_football_agent
from utils import make_user_id

COMMANDS = {
    "/football": {
        "description": "Football enthusiast and analyst agent",
        "agent": get_football_agent()
    }
}

command_completer = WordCompleter(
    list(COMMANDS.keys()),
    ignore_case=True,
    sentence=True,
    meta_dict={cmd: COMMANDS[cmd]["description"] for cmd in COMMANDS}
)

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})

async def main():
    user_id = make_user_id()
    session = PromptSession(
        completer=command_completer,
        complete_while_typing=True,
        style=style,
    )

    print(f"\n Commands: {', '.join(COMMANDS.keys())}")
    print(f"Type '/exit' to quit\n")
    print(f"User ID: {user_id}")

    while True:
        try:
            user_input = await session.prompt_async("> ", completer=command_completer)
            user_input = user_input.strip()

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