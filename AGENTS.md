# Repository Guidelines

## Project Structure & Module Organization
- Application code lives in `src/substack_mcp/` with modular files for HTTP (`client.py`), API surface (`server.py`), analytics, parsers, and settings.
- Command-line helpers sit in `scripts/`; use `scripts/run_server.py` for local FastAPI runs and `run_mcp_with_venv.sh` for MCP stdio integration.
- Tests reside in `tests/` with fixtures under `tests/fixtures/`; keep new fixtures small and deterministic.
- Deployment metadata (`Procfile`, `railway.toml`, `runtime.txt`) and docs (`README.md`, `MCP_SETUP.md`, `TROUBLESHOOTING.md`) live at the repository root.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate` — create and enter a local virtual environment.
- `pip install -e .[dev]` — install the package in editable mode along with pytest tooling.
- `python scripts/run_server.py --port 8080` — start the REST API locally; honours `HOST`, `PORT`, `LOG_LEVEL`, and `SUBSTACK_MCP_WARM_PUBLICATION` env vars.
- `./run_mcp_with_venv.sh` — boot the MCP stdio server used by Claude Desktop integrations.
- `railway up` — trigger a Railway deploy using the provided Nixpacks configuration.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation; prefer descriptive snake_case for functions, methods, and variables.
- Type hints are required for public functions; favour Pydantic models for data contracts.
- Keep modules cohesive (HTTP in `client.py`, parsing in `parsers.py`, etc.) and add succinct comments only for non-obvious logic.
- Run `pyflakes` or `ruff` if added to catch unused imports prior to committing.

## Testing Guidelines
- Use `pytest` (asyncio plugin enabled) for unit and integration tests: `pytest` or `pytest tests/test_analysis.py`.
- Name new test modules `test_<feature>.py` and match async tests with `pytest.mark.asyncio`.
- Leverage fixtures for HTML/RSS samples; avoid live network calls by mocking `httpx` via `respx`.
- Aim to cover new parsing logic and analytics branches; include regression tests when fixing bugs.

## Commit & Pull Request Guidelines
- Write imperative, scope-focused commits (e.g., `Add root middleware for connectors`).
- Reference issues or tickets in the commit body when applicable; keep commits logically isolated for easy review.
- PRs should summarize behaviour changes, list impacted endpoints or modules, and describe testing performed (`pytest`, manual `/health` checks, etc.).
- Attach screenshots or logs for deployment or connector-facing changes, especially when touching Railway configuration.

## Security & Deployment Notes
- Respect Substack rate limits: tweak throttling via `SUBSTACK_MCP_THROTTLE` before production deploys.
- Never commit real API keys; configure secrets through Railway or local `.env` files excluded from git.
- Validate `/health` after each deploy and monitor Railway logs for 404 probes from ChatGPT connectors.
