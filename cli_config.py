import logging
import warnings
import shutil
import textwrap

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

# ANSI color codes
GRAY = "\033[90m"
RESET = "\033[0m"
FINAL_MARKER = "---FINAL---"

EXIT_COMMANDS = {"/exit", "/quit", "/q", ":wq", ":q"}

COMMANDS = {
    "/help": {"description": "Show commands and internal agent architecture"},
    "/clear": {"description": "Clear terminal screen"},
    "/exit": {"description": "Exit CLI"},
}

CLI_STYLE = Style.from_dict({
    "completion-menu.completion": "bg:#008888 #ffffff",
    "completion-menu.completion.current": "bg:#00aaaa #000000",
    "scrollbar.background": "bg:#88aaaa",
    "scrollbar.button": "bg:#222222",
})


def configure_runtime_logging():
    """Suppress known harmless framework warnings/noise in CLI output."""
    warnings.filterwarnings("ignore", message="Failed to detach context")
    logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
    logging.getLogger("opentelemetry.context").setLevel(logging.CRITICAL)


def get_commands():
    return COMMANDS


def build_command_completer(commands):
    return WordCompleter(
        list(commands.keys()),
        ignore_case=True,
        sentence=True,
        meta_dict={cmd: commands[cmd]["description"] for cmd in commands},
    )

def _print_startup_capabilities():
    raw_lines = [
        "STRANDS LAB CLI",
        "Capabilities:",
        "  - Football intelligence via football_agent (22 tools: fixtures, tables, team/player stats, previews, transfers)",
        "  - Job support via jobs_agent swarm (resume analysis, job search, fit scoring, persistence, application support)",
        "  - General conversation via chat_agent",
        "  - Automatic intent routing across agents",
        "",
        "Example queries:",
        "  - \"How's the Premier League table looking?\"",
        "  - \"Did Bruno Fernandes score in the latest game?\"",
        "  - \"Analyze my resume\"",
    ]

    terminal_width = shutil.get_terminal_size(fallback=(120, 30)).columns
    # +4 accounts for "| " + " |" box chrome.
    max_content_width = max(1, terminal_width - 4)

    lines: list[str] = []
    for line in raw_lines:
        if line.startswith("  - "):
            wrapper = textwrap.TextWrapper(
                width=max_content_width,
                initial_indent="  - ",
                subsequent_indent="    ",
                break_long_words=False,
                break_on_hyphens=False,
            )
            lines.extend(wrapper.wrap(line[4:]))
        else:
            wrapper = textwrap.TextWrapper(
                width=max_content_width,
                break_long_words=False,
                break_on_hyphens=False,
            )
            lines.extend(wrapper.wrap(line) or [""])

    width = min(max(len(line) for line in lines), max_content_width)
    border = "+" + "-" * (width + 2) + "+"

    print()
    print(border)
    for line in lines:
        print(f"| {line.ljust(width)} |")
    print(border)



