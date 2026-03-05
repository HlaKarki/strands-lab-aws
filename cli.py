import asyncio

from utils import make_user_id
from prompt_toolkit.styles import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from services.fotmob import FotmobClient

fb_client = FotmobClient()

COMMANDS = {
    "/football": {
        "description": "Football enthusiast and analyst agent",
        "agent": fb_client.get_football_agent()
    },
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

seen_tools = set()

def process_event(event, debug=False):
    if debug:
        if event.get("init_event_loop", False):
            print("> Event loop initialized")
        elif event.get("start_event_loop", False):
            print("> Event loop cycle starting")
        elif "message" in event:
            print(f"> New message created: {event['message']['role']}")
        elif "result" in event:
            print("> Agent completed with result")
        elif event.get("force_stop", False):
            print(f"> Event loop force-stopped: {event.get('force_stop_reason', 'unknown reason')}")

    if "current_tool_use" in event and event["current_tool_use"].get("name"):
        tool = event["current_tool_use"]
        tool_name = tool["name"]
        tool_id = tool.get("toolUseId")
        if tool_name and tool_id and tool_id not in seen_tools:
            seen_tools.add(tool_id)
            print(f"⚙︎ Using tool: {tool_name}")

    if "data" in event:
        print(event["data"], end="", flush=True)

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

            # Streaming
            print()
            async for event in agent.stream_async(message):
                process_event(event)
            print()

        except KeyboardInterrupt:
            # save conversation/progress
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())