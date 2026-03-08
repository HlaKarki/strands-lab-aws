from typing import Any

from cli_config import FINAL_MARKER, GRAY, RESET


class StreamRenderer:
    """Handles streaming output styling and event processing for agent responses."""

    def __init__(self):
        self.seen_tools: set[str] = set()
        self.thinking_mode = True
        self.marker_buffer = ""
        self.last_output_ended_with_newline = True

    def start_turn(self):
        self.seen_tools.clear()
        self._reset_thinking_phase()

    def finish_turn(self):
        self._flush_stream_buffer()
        print()

    @staticmethod
    def _longest_marker_prefix(text: str) -> int:
        """Return the longest suffix in text that matches a FINAL_MARKER prefix."""
        max_prefix = min(len(text), len(FINAL_MARKER) - 1)
        for size in range(max_prefix, 0, -1):
            if text.endswith(FINAL_MARKER[:size]):
                return size
        return 0

    def _emit_text(self, text: str, grey: bool):
        if not text:
            return
        if grey:
            print(f"{GRAY}{text}{RESET}", end="", flush=True)
        else:
            print(text, end="", flush=True)
        self.last_output_ended_with_newline = text.endswith("\n")

    def _stream_data(self, text: str):
        """
        Stream text with thinking/final styling.
        - Grey while in thinking mode
        - Switch to normal once FINAL_MARKER is seen
        - Hide FINAL_MARKER from terminal output
        - Handle marker split across chunks
        """
        if not text:
            return

        combined = self.marker_buffer + text
        self.marker_buffer = ""

        while True:
            marker_index = combined.find(FINAL_MARKER)
            if marker_index == -1:
                break

            self._emit_text(combined[:marker_index], grey=self.thinking_mode)
            self.thinking_mode = False
            combined = combined[marker_index + len(FINAL_MARKER):]

        partial_marker_len = self._longest_marker_prefix(combined)
        if partial_marker_len:
            visible_text = combined[:-partial_marker_len]
            self.marker_buffer = combined[-partial_marker_len:]
        else:
            visible_text = combined

        self._emit_text(visible_text, grey=self.thinking_mode)

    def _flush_stream_buffer(self):
        """Flush any remaining buffered text (e.g., incomplete FINAL_MARKER fragments)."""
        if self.marker_buffer:
            self._emit_text(self.marker_buffer, grey=self.thinking_mode)
            self.marker_buffer = ""

    def _reset_thinking_phase(self):
        """Reset styling state for the next agent/node reasoning phase."""
        if not self.thinking_mode and not self.last_output_ended_with_newline:
            print()
            self.last_output_ended_with_newline = True
        self.thinking_mode = True
        self.marker_buffer = ""

    def _print_tool_use(self, tool_name: str):
        if self.thinking_mode:
            print(f"\n{GRAY}⚙︎ Using tool: {tool_name}{RESET}")
        else:
            print(f"\n⚙︎ Using tool: {tool_name}")
        self.last_output_ended_with_newline = True

    def process_event(self, event: dict[str, Any], debug: bool = False):
        """
        Process streaming events from Graph/Swarm execution.
        Based on: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/streaming/
        """
        event_type = event.get("type")

        # === Multi-Agent Graph Events ===
        if event_type == "multiagent_node_start":
            self._reset_thinking_phase()
            if debug:
                print(f"\n🔄 Node '{event.get('node_id')}' starting...")
            return

        if event_type == "multiagent_node_stream":
            inner_event = event.get("event", {})
            inner_type = inner_event.get("type")

            if inner_type in {"multiagent_node_start", "multiagent_handoff"}:
                self._reset_thinking_phase()
                return

            # Handle nested multi-agent events (e.g., Swarm inside Graph)
            if inner_type == "multiagent_node_stream":
                nested_event = inner_event.get("event", {})
                nested_type = nested_event.get("type")

                if nested_type in {"multiagent_node_start", "multiagent_handoff"}:
                    self._reset_thinking_phase()
                    return

                if "data" in nested_event:
                    self._stream_data(nested_event["data"])

                if "current_tool_use" in nested_event and nested_event["current_tool_use"].get("name"):
                    tool = nested_event["current_tool_use"]
                    tool_name = tool["name"]
                    tool_id = tool.get("toolUseId")
                    if tool_name and tool_id and tool_id not in self.seen_tools:
                        self.seen_tools.add(tool_id)
                        self._print_tool_use(tool_name)
                return

            if "data" in inner_event:
                self._stream_data(inner_event["data"])

            if "current_tool_use" in inner_event and inner_event["current_tool_use"].get("name"):
                tool = inner_event["current_tool_use"]
                tool_name = tool["name"]
                tool_id = tool.get("toolUseId")
                if tool_name and tool_id and tool_id not in self.seen_tools:
                    self.seen_tools.add(tool_id)
                    self._print_tool_use(tool_name)
            return

        if event_type == "multiagent_node_stop":
            if debug:
                print(f"\n✅ Node '{event.get('node_id')}' completed")
            return

        if event_type == "multiagent_handoff":
            self._reset_thinking_phase()
            if debug:
                from_node = event.get("from_node_id", "unknown")
                to_node = event.get("to_node_id", "unknown")
                print(f"\n🔀 Handoff: {from_node} → {to_node}")
            return

        if event_type == "multiagent_result":
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
            if tool_name and tool_id and tool_id not in self.seen_tools:
                self.seen_tools.add(tool_id)
                self._print_tool_use(tool_name)
            return

        if "data" in event:
            self._stream_data(event["data"])
            return

        if "result" in event and debug:
            print("> Agent completed with result")
            return

        if "force_stop" in event and debug:
            print(f"> Event loop force-stopped: {event.get('force_stop_reason', 'unknown')}")
            return
