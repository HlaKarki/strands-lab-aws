import asyncio
import warnings
import logging

from services.orchestrator import Orchestrator

# Suppress OpenTelemetry context warnings (harmless framework bugs)
warnings.filterwarnings("ignore", message="Failed to detach context")
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)

from services.job_swarm import JobSwarm
from utils import make_user_id
from prompt_toolkit.styles import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from services.fotmob import FotmobClient

fb_client = FotmobClient()
job_swarm = JobSwarm()

COMMANDS = {
    "/football": {
        "description": "Football enthusiast and analyst agent",
        "agent": fb_client.get_football_agent()
    },
    "/job_swarm": {
        "description": "Job finder and assistant built as strands swarm agent",
        "agent": job_swarm.get_job_application_swarm()
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

seen_tools = set()

def process_event(event, debug=False):
    # Debug logging
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
        elif event.get("type") == "multiagent_node_start":
            print(f"\n> Agent '{event.get('node_id')}' starting...")
        elif event.get("type") == "multiagent_handoff":
            from_node = event.get("from_node_id", "unknown")
            to_node = event.get("to_node_id", "unknown")
            print(f"\n> Handoff: {from_node} → {to_node}")

    # Swarm streaming (multiagent_node_stream contains inner events)
    if event.get("type") == "multiagent_node_stream":
        inner_event = event.get("event", {})

        if "data" in inner_event:
            print(inner_event["data"], end="", flush=True)

        if "current_tool_use" in inner_event and inner_event["current_tool_use"].get("name"):
            tool = inner_event["current_tool_use"]
            tool_name = tool["name"]
            tool_id = tool.get("toolUseId")
            if tool_name and tool_id and tool_id not in seen_tools:
                seen_tools.add(tool_id)
                print(f"⚙︎ Using tool: {tool_name}")
        return

    # Single agent events
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
    orchestrator = Orchestrator(user_id)
    graph = orchestrator.get_graph()

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

            # Reset thinking/final state for new message
            seen_tools.clear()

            # Streaming
            async for event in graph.stream_async(user_input):
                process_event(event, debug=False)
            print()

        except KeyboardInterrupt:
            # save conversation/progress
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())