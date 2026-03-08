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
thinking_mode = True  # Track if we're in thinking or final output mode
marker_buffer = ""

# ANSI color codes
GRAY = "\033[90m"
RESET = "\033[0m"
FINAL_MARKER = "---FINAL---"


def _longest_marker_prefix(text: str) -> int:
    """Return the longest suffix in text that matches a FINAL_MARKER prefix."""
    max_prefix = min(len(text), len(FINAL_MARKER) - 1)
    for size in range(max_prefix, 0, -1):
        if text.endswith(FINAL_MARKER[:size]):
            return size
    return 0


def _emit_text(text: str, grey: bool):
    if not text:
        return
    if grey:
        print(f"{GRAY}{text}{RESET}", end="", flush=True)
    else:
        print(text, end="", flush=True)


def _stream_data(text: str):
    """
    Stream text with thinking/final styling.
    - Grey while in thinking mode
    - Switch to normal once FINAL_MARKER is seen
    - Hide FINAL_MARKER from terminal output
    - Handle marker split across chunks
    """
    global thinking_mode, marker_buffer
    if not text:
        return

    combined = marker_buffer + text
    marker_buffer = ""

    while True:
        marker_index = combined.find(FINAL_MARKER)
        if marker_index == -1:
            break

        _emit_text(combined[:marker_index], grey=thinking_mode)
        thinking_mode = False
        combined = combined[marker_index + len(FINAL_MARKER):]

    partial_marker_len = _longest_marker_prefix(combined)
    if partial_marker_len:
        visible_text = combined[:-partial_marker_len]
        marker_buffer = combined[-partial_marker_len:]
    else:
        visible_text = combined

    _emit_text(visible_text, grey=thinking_mode)


def _flush_stream_buffer():
    """Flush any remaining buffered text (e.g., incomplete FINAL_MARKER fragments)."""
    global marker_buffer
    if marker_buffer:
        _emit_text(marker_buffer, grey=thinking_mode)
        marker_buffer = ""


def _print_tool_use(tool_name: str):
    if thinking_mode:
        print(f"\n{GRAY}⚙︎ Using tool: {tool_name}{RESET}")
    else:
        print(f"\n⚙︎ Using tool: {tool_name}")

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
                _stream_data(nested_event["data"])

            # Track tool usage from nested agent
            if "current_tool_use" in nested_event and nested_event["current_tool_use"].get("name"):
                tool = nested_event["current_tool_use"]
                tool_name = tool["name"]
                tool_id = tool.get("toolUseId")
                if tool_name and tool_id and tool_id not in seen_tools:
                    seen_tools.add(tool_id)
                    _print_tool_use(tool_name)
            return

        # Handle direct agent events (single level)
        if "data" in inner_event:
            _stream_data(inner_event["data"])

        # Track tool usage
        if "current_tool_use" in inner_event and inner_event["current_tool_use"].get("name"):
            tool = inner_event["current_tool_use"]
            tool_name = tool["name"]
            tool_id = tool.get("toolUseId")
            if tool_name and tool_id and tool_id not in seen_tools:
                seen_tools.add(tool_id)
                _print_tool_use(tool_name)
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
            _print_tool_use(tool_name)
        return

    if "data" in event:
        _stream_data(event["data"])
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

            # Reset state for new message
            seen_tools.clear()
            global thinking_mode, marker_buffer
            thinking_mode = True
            marker_buffer = ""

            # Stream events from graph execution
            async for event in graph.stream_async(user_input):
                process_event(event, debug=False)

            _flush_stream_buffer()
            print()

        except KeyboardInterrupt:
            # save conversation/progress
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    asyncio.run(main())
