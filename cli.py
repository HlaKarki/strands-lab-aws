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
    """
    Process streaming events from Graph/Swarm execution.
    Based on: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/streaming/
    """
    event_type = event.get("type")

    # === Multi-Agent Graph Events ===

    # Node execution start
    if event_type == "multiagent_node_start":
        if debug:
            print(f"\n🔄 Node '{event.get('node_id')}' starting...")
        return

    # Streaming events from within a node
    if event_type == "multiagent_node_stream":
        inner_event = event.get("event", {})

        # Handle nested multi-agent events (e.g., Swarm inside Graph)
        if inner_event.get("type") == "multiagent_node_stream":
            # Extract the deeply nested event
            nested_event = inner_event.get("event", {})

            # Stream text output from nested agent
            if "data" in nested_event:
                print(nested_event["data"], end="", flush=True)

            # Track tool usage from nested agent
            if "current_tool_use" in nested_event and nested_event["current_tool_use"].get("name"):
                tool = nested_event["current_tool_use"]
                tool_name = tool["name"]
                tool_id = tool.get("toolUseId")
                if tool_name and tool_id and tool_id not in seen_tools:
                    seen_tools.add(tool_id)
                    print(f"\n⚙︎ Using tool: {tool_name}")
            return

        # Handle direct agent events (single level)
        if "data" in inner_event:
            print(inner_event["data"], end="", flush=True)

        # Track tool usage
        if "current_tool_use" in inner_event and inner_event["current_tool_use"].get("name"):
            tool = inner_event["current_tool_use"]
            tool_name = tool["name"]
            tool_id = tool.get("toolUseId")
            if tool_name and tool_id and tool_id not in seen_tools:
                seen_tools.add(tool_id)
                print(f"\n⚙︎ Using tool: {tool_name}")
        return

    # Node execution completion
    if event_type == "multiagent_node_stop":
        if debug:
            print(f"\n✅ Node '{event.get('node_id')}' completed")
        return

    # Handoff between agents (Swarm)
    if event_type == "multiagent_handoff":
        if debug:
            from_node = event.get("from_node_id", "unknown")
            to_node = event.get("to_node_id", "unknown")
            print(f"\n🔀 Handoff: {from_node} → {to_node}")
        return

    # Final graph/swarm result - DO NOT PRINT (already streamed)
    if event_type == "multiagent_result":
        # Result already streamed via multiagent_node_stream events
        return

    # === Single Agent Events (fallback for non-graph agents) ===

    if "init_event_loop" in event and debug:
        print("> Event loop initialized")
        return

    if "start_event_loop" in event and debug:
        print("> Event loop cycle starting")
        return

    if "message" in event and debug:
        print(f"> New message created: {event['message']['role']}")
        return

    if "current_tool_use" in event and event["current_tool_use"].get("name"):
        tool = event["current_tool_use"]
        tool_name = tool["name"]
        tool_id = tool.get("toolUseId")
        if tool_name and tool_id and tool_id not in seen_tools:
            seen_tools.add(tool_id)
            print(f"\n⚙︎ Using tool: {tool_name}")
        return

    if "data" in event:
        print(event["data"], end="", flush=True)
        return

    if "result" in event and debug:
        print("> Agent completed with result")
        return

    if "force_stop" in event and debug:
        print(f"> Event loop force-stopped: {event.get('force_stop_reason', 'unknown')}")
        return


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

            # Reset tool tracking for new message
            seen_tools.clear()

            # Stream events from graph execution
            async for event in graph.stream_async(user_input):
                process_event(event, debug=False)

            # Add newline after streaming completes
            print()

        except KeyboardInterrupt:
            # save conversation/progress
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())