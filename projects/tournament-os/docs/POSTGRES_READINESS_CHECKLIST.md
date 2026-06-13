# PostgreSQL Readiness Checklist

Status: Working readiness checklist for Phase 1 handoff.

Purpose:
Make the PostgreSQL path repeatable before the system is opened for internal user testing.

## Current State

- `backend/docker-compose.yml` provides PostgreSQL 16.
- `.env.example` points to `postgresql+psycopg://tournament_os:tournament_os@localhost:5433/tournament_os`.
- Alembic is configured under `backend/migrations/`.
- Initial migration exists at `backend/migrations/versions/20260612_0001_initial_phase_1_schema.py`.
- The initial migration includes the Phase 1 official write model plus read/integration tables such as `event_outbox`, `tournament_dashboard_summaries`, `leaderboard_snapshots`, `player_status_snapshots`, and `discord_message_jobs`.
- `scripts/smoke_phase1.py` now follows the score lifecycle: create score, submit, verify, approve.

## Verified Locally

These commands have been verified with SQLite smoke mode:

```powershell
Set-Location E:\TTLIVE\projects\tournament-os\backend
$env:TOURNAMENT_OS_DATABASE_URL='sqlite:///./tmp_smoke_phase1.db'
python scripts\smoke_phase1.py --create-schema
```

Result:

```text
16 registrations
2 stages
3 groups
7 rounds
32 qualifier scores
8 advanced players
24 final scores
winner selected
```

The temporary SQLite database was removed after the smoke run.

## PostgreSQL Readiness Commands

Run from `E:\TTLIVE\projects\tournament-os\backend`:

```powershell
docker compose up -d postgres
$env:TOURNAMENT_OS_DATABASE_URL='postgresql+psycopg://tournament_os:tournament_os@localhost:5433/tournament_os'
alembic upgrade head
python scripts\smoke_phase1.py
python -m unittest discover -s tests -v
```

Optional local server check:

```powershell
python -m uvicorn tournament_os.api.main:app --host 127.0.0.1 --port 8010
```

Open:

```text
http://127.0.0.1:8010/
http://127.0.0.1:8010/web/tournaments/{public_slug}
http://127.0.0.1:8010/web/tournaments/{public_slug}/stream
```

## Acceptance Checklist

- PostgreSQL container starts healthy.
- `alembic upgrade head` completes without manual schema edits.
- `scripts/smoke_phase1.py` completes against PostgreSQL without `--create-schema`.
- Backend tests pass after the PostgreSQL smoke run.
- Generated public and stream pages load for the smoke tournament.
- Leaderboard/export responses do not include contact value, Discord ID, private evidence, admin notes, or audit payloads.
- Any generated smoke data is clearly disposable.

## Known Gaps

- Backend tests still primarily use SQLite in-memory databases.
- Auth/authorization for admin endpoints is not production-ready.
- The web admin surface is still a basic server-rendered console, not a full interactive workflow.
- Discord bot is an early adapter; score submission remains intentionally disabled.
- Scratch/debug artifacts remain in the worktree and must be removed or ignored before commit.

## Agent B Assignment For 2026-06-13 19:00

Agent B should not repeat L2 Score Lifecycle or L4 Export implementation.

Agent B should focus on:

1. Run the PostgreSQL readiness commands above.
2. Record exact pass/fail output in `AGENT_COORDINATION.md`.
3. If PostgreSQL smoke fails, fix only PostgreSQL/migration/smoke-script blockers.
4. Do not implement frontend, full Discord automation, OCR, payment, SaaS, or overlay editor.
5. Do not delete scratch/debug files unless the user explicitly approves cleanup or Agent A marks them safe to remove.

If PostgreSQL readiness passes, the next system priority is cleanup and commit preparation.

