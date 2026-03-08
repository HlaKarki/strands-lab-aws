import getpass
import sys
from pathlib import Path

from dotenv import load_dotenv

REQUIRED_KEYS = [
    "AWS_REGION",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "BEDROCK_MODEL_ID",
]

DEFAULT_VALUES = {
    "AWS_REGION": "us-east-2",
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
}

PLACEHOLDER_VALUES = {
    "AWS_ACCESS_KEY_ID": "your_access_key_here",
    "AWS_SECRET_ACCESS_KEY": "your_secret_key_here",
}

SECRET_KEYS = {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"}


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def _is_missing(key: str, value: str | None) -> bool:
    if value is None:
        return True
    if not value.strip():
        return True
    return PLACEHOLDER_VALUES.get(key) == value.strip()


def _prompt_for_value(key: str, current_value: str | None) -> str:
    default_value = None if _is_missing(key, current_value) else current_value
    if default_value is None:
        default_value = DEFAULT_VALUES.get(key)

    prompt = f"{key}"
    if default_value:
        prompt += f" [{default_value}]"
    prompt += ": "

    while True:
        if key in SECRET_KEYS:
            user_input = getpass.getpass(prompt)
        else:
            user_input = input(prompt)

        user_input = user_input.strip()
        if not user_input and default_value:
            return default_value
        if user_input:
            return user_input
        print(f"{key} is required.")


def _upsert_env_file(path: Path, updates: dict[str, str]):
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    line_index_by_key: dict[str, int] = {}

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key = stripped.split("=", 1)[0].strip()
        line_index_by_key[key] = index

    for key, value in updates.items():
        rendered = f"{key}={value}"
        if key in line_index_by_key:
            lines[line_index_by_key[key]] = rendered
        else:
            lines.append(rendered)

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def ensure_env_ready(project_root: str = "."):
    """
    Ensure required env vars exist on first run.
    If missing/incomplete, prompt user and write values into .env.
    """
    root = Path(project_root).resolve()
    env_path = root / ".env"
    env_example_path = root / ".env.example"

    if not env_path.exists() and env_example_path.exists():
        env_path.write_text(env_example_path.read_text(encoding="utf-8"), encoding="utf-8")

    current_values = _parse_env_file(env_path)
    missing_keys = [key for key in REQUIRED_KEYS if _is_missing(key, current_values.get(key))]
    if not missing_keys:
        load_dotenv(dotenv_path=env_path, override=True)
        return

    if not sys.stdin.isatty():
        missing = ", ".join(missing_keys)
        raise RuntimeError(
            f"Missing required environment values: {missing}. "
            "Run with a TTY once to complete setup, or populate .env manually."
        )

    print("\nFirst-run setup: your .env is missing required values.")
    print("Please provide the following configuration values:\n")

    updates = {}
    for key in missing_keys:
        updates[key] = _prompt_for_value(key, current_values.get(key))

    _upsert_env_file(env_path, updates)
    env_path.chmod(0o600)
    load_dotenv(dotenv_path=env_path, override=True)
    print("\nEnvironment setup complete. Values saved to .env\n")
