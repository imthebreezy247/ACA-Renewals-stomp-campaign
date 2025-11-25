# Repository Guidelines

## Project Structure & Module Organization

- Core scripts: extract_all_deals-properly-mcp.py (production multi-agent sweep), extract_all_daniel_hera_deals.py (legacy single-agent run), and extract_single_email.py (interactive debugger); docs live in README.md, USAGE_GUIDE.md, and setup guides.
- Helpers: mcp_functions.py wraps Gmail/Drive/Slack calls; create_tables.py and setup_database.py prepare Supabase tables; supabase_schema.sql holds the schema.
- Runtime assets: attachments/ stores downloaded files by thread ID, exports/ stores CSV outputs, .env carries secrets, and credentials.json/token.json support Gmail OAuth.

## Build, Test, and Development Commands

- pip install -r requirements.txt installs Anthropic, Supabase, Gmail API, dotenv, tqdm, and logging deps.
- python verify_setup.py runs pre-flight checks for env vars, credentials, and Supabase reachability.
- python extract_all_deals-properly-mcp.py --max 5 --agent `danielberman.ushealth@gmail.com` exercises the main pipeline; add --auto-save to push to Supabase and --no-csv to skip file export.
- python extract_single_email.py walks one email end-to-end for quick debugging.
- python extract_all_daniel_hera_deals.py keeps compatibility with the original Daniel Hera-only workflow.

## Coding Style & Naming Conventions

- Python 3.10+, 4-space indents, f-strings, and type hints; prefer pathlib.Path for filesystem work and logging over print for runtime notes.
- Keep configuration in the top-level CONFIG dict and surface new knobs via env vars loaded through .env + dotenv.
- Export and attachment names should stay timestamped (YYYYMMDD_HHMMSS) and include the agent email when available.

## Testing Guidelines

- No formal test suite; run python verify_setup.py before changes, then python extract_all_deals-properly-mcp.py --max 1 --no-csv as a smoke test.
- When touching Supabase logic, confirm duplicates are checked before inserts and skim extraction.log for new warnings.
- Capture representative CLI output in PRs to prove the pipeline completes with your flags.

## Commit & Pull Request Guidelines

- Recent history leans on conventional prefixes (feat:, fix:); prefer imperative, scope-limited summaries such as feat: add agent sweep flag.
- PRs should describe purpose, commands run, and data touchpoints (Supabase, Drive, Slack); include logs or screenshots if behavior changed.
- Never commit secrets (.env, credentials.json, token.json); generated exports and attachments should remain gitignored.
