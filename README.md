# Strands Lab AWS

CLI-based multi-agent assistant built with Strands on AWS Bedrock.

## What It Does

- Automatically routes user requests across:
  - `football_agent` (22 football tools)
  - `jobs_agent` (resume + job-finder swarm)
  - `chat_agent` (general conversation)
- Streams output with thinking (gray) vs final answer (normal)
- Persists sessions per generated user ID
- Includes first-run `.env` bootstrap prompting

## Requirements

- Python `>=3.11`
- [`uv`](https://docs.astral.sh/uv/)
- AWS Bedrock access for the model in your configured region

## Install

```bash
uv sync
uv run install-browsers  # Install Playwright Chromium for football agent scraping
```

## Run

```bash
uv run cli.py
```

On first run, if `.env` is missing/incomplete, the app prompts for required keys and writes `.env`:

- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `BEDROCK_MODEL_ID`

## CLI Commands

- `/help` show commands + internal agent overview
- `/clear` clear terminal
- `/exit` exit CLI  
  also supports: `/quit`, `/q`, `:q`, `:wq`

## Resume Loading Behavior

When resume analysis is requested, `load_resume`:

1. Prompts for pasted/dragged resume path
2. If sample exists, allows Enter to use sample
3. Loads `.pdf` or `.txt`

Default sample path lookup:

- `/resumes/sample/hla.sample.pdf`
- `<repo>/resumes/sample/hla.sample.pdf`

## Project Layout

- `cli.py` - CLI entrypoint and prompt loop
- `cli_config.py` - CLI config/styles/command metadata/startup banner
- `cli_stream_renderer.py` - event stream rendering logic
- `env_bootstrap.py` - first-run env setup helper
- `services/orchestrator.py` - graph orchestration and routing
- `services/fotmob.py` - football tools
- `services/job_swarm.py` - job swarm and resume/job tooling
