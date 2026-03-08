import asyncio

from prompt_toolkit import PromptSession
from cli_config import (
    CLI_STYLE,
    EXIT_COMMANDS,
    _print_startup_capabilities,
    build_command_completer,
    configure_runtime_logging,
    get_commands,
)
from cli_stream_renderer import StreamRenderer
from env_bootstrap import ensure_env_ready
from services.orchestrator import Orchestrator
from utils import make_user_id

configure_runtime_logging()


def _clear_screen():
    # ANSI clear screen + cursor home
    print("\033[2J\033[H", end="")

def _print_help(commands):
    print("\nAVAILABLE COMMANDS")
    for cmd, metadata in commands.items():
        print(f"  {cmd:<20} {metadata['description']}")

    print("\nINTERNAL AGENTS")
    print("  1. football_agent")
    print("     - Specialized football/soccer assistant")
    print("     - Uses 22 tools (fixtures, tables, team data, player data, stats, previews, transfers, etc.)")
    print("  2. jobs_agent (Job Swarm)")
    print("     - Multi-agent swarm for job workflows")
    print("     - Includes resume analysis, job finding, persistence, fit scoring, and application support")
    print("\nRouting: normal messages are auto-routed across available agents.\n")

def _handle_local_command(user_input, commands):
    if user_input == "/help":
        _print_help(commands)
        return True, None

    if user_input == "/clear":
        _clear_screen()
        return True, None

    return False, None


async def main():
    ensure_env_ready()

    commands = get_commands()
    command_completer = build_command_completer(commands)
    renderer = StreamRenderer()

    user_id = make_user_id()
    orchestrator = Orchestrator(user_id)
    graph = orchestrator.get_graph()

    session = PromptSession(
        completer=command_completer,
        complete_while_typing=True,
        style=CLI_STYLE,
    )

    _print_startup_capabilities()
    print("\n Commands: /help, /clear, /exit")
    print("Type '/help' to see all commands\n")
    print(f"User ID: {user_id}")

    while True:
        try:
            user_input = await session.prompt_async("> ", completer=command_completer)
            user_input = user_input.strip()

            if not user_input:
                continue

            if user_input in EXIT_COMMANDS:
                break

            handled, command_routed_input = _handle_local_command(user_input, commands)
            if handled and command_routed_input is None:
                continue

            effective_input = command_routed_input or user_input

            renderer.start_turn()
            async for event in graph.stream_async(effective_input):
                renderer.process_event(event, debug=False)

            renderer.finish_turn()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
