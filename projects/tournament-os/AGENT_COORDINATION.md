# Agent Coordination

Purpose:
Use this file as the shared coordination point between AI agents working on Tournament OS.
Agents may read and update this file to coordinate implementation, tests, reviews, and handoffs without changing source code or core specifications unexpectedly.

This file is coordination-only. It must not become the source of truth for business rules.

## Ground Rules

- Read `AGENTS.md` first.
- Read `DASHBOARD.md` before repo-wide work.
- For Tournament OS work, read these before editing:
  - `projects/tournament-os/SYSTEM_BOUNDARY.md`
  - `projects/tournament-os/PROJECT_CONTEXT.md`
  - all files under `projects/tournament-os/spec/`
  - `projects/tournament-os/docs/TEST_PLAN_PHASE_1.md`
- Do not implement payment, mobile app, SaaS, full Discord automation, OCR automation, or advanced OBS control unless the user explicitly changes scope.
- PostgreSQL is the source of truth.
- FastAPI owns business logic.
- Discord, bot, overlay, and public pages must only submit or display backend data.
- Do not store secrets, stream keys, tokens, payment details, or private player contact data in Git.
- Do not overwrite another agent's work. If a file has unexpected changes, inspect and coordinate here first.
- Before commit or push, run the relevant tests and record results in this file.

## Shared Workflow

1. Claim a task in the Task Board.
2. Read the required docs for that task.
3. Record the intended files before editing.
4. Make a small focused change.
5. Run tests or smoke checks.
6. Update this file with:
   - what changed
   - files touched
   - commands run
   - results
   - risks or blockers
   - next action
7. Leave the task either `done`, `blocked`, or `ready for review`.

## Agent Roles

### Agent A: System Builder

Primary responsibility:
Implement backend features and keep source code aligned with specifications.

Typical work:

- FastAPI routes
- SQLAlchemy models
- Alembic migrations
- service layer business logic
- public/private serializers
- audit/event records
- smoke scripts

Must protect:

- business rules in backend services
- PostgreSQL schema consistency
- no private data in public endpoints
- no integration logic calculating tournament results outside backend

### Agent B: Test And Review Agent

Primary responsibility:
Expand coverage, verify behavior, and review implementation against specs.

Typical work:

- unit tests
- service tests
- integration tests
- public/privacy tests
- stream-safe endpoint tests
- smoke test documentation
- review notes and bug reports

Must protect:

- Phase 1 test plan coverage
- regression safety
- privacy boundaries
- state transition correctness
- concurrency-sensitive flows

### Shared Responsibility

Both agents may update documentation only when the reason, next action, and risks are recorded.

## Current Repository Snapshot

Last checked by Codex: 2026-06-12.

Known status:

- Tournament OS backend files are actively changing.
- Current unit test command passed:

```powershell
python -m unittest discover -s projects\tournament-os\backend\tests
```

Result:

```text
Ran 22 tests
OK
```

- SQLite smoke command passed:

```powershell
Set-Location projects\tournament-os\backend
$env:TOURNAMENT_OS_DATABASE_URL="sqlite:///./tournament_os_smoke_check.db"
python scripts\smoke_phase1.py --create-schema
```

Result:

- created 16 registrations
- generated groups, rounds, and check-in sessions
- approved scores
- calculated leaderboard
- advanced top players
- assigned final
- calculated winner

Temporary smoke database was removed after the check.

## Task Board

| ID | Owner | Status | Task | Files / Area | Notes |
| :--- | :--- | :---: | :--- | :--- | :--- |
| TOS-001 | Agent B | done | Review current backend changes and identify risky or incomplete files before commit. | `projects/tournament-os/backend/` | Completed 2026-06-12. See update log. |
| TOS-002 | Agent B | done | Compare existing tests against `docs/TEST_PLAN_PHASE_1.md`. | `projects/tournament-os/backend/tests/` | Missing-test checklist filled in below. |
| TOS-003 | Agent A | done | Verify API routes use public-safe serializers where required. | `tournament_os/api/routers/`, `tournament_os/domain/serializers.py` | Public leaderboard/groups use safe DTOs; targeted privacy scan completed. |
| TOS-004 | Agent A | done | Verify migrations match current models. | `migrations/`, `tournament_os/models/` | Added missing `overlay_configs` migration table. PostgreSQL smoke blocked by local auth; SQLite smoke passed. |
| TOS-005 | Agent B | done | Add missing tests for check-in windows, registration capacity, and score state machine. | `tests/test_checkins.py`, `tests/test_capacity.py`, `tests/test_score_lifecycle.py` | Tests pass after Agent A service fixes. |
| TOS-006 | Agent B | done | Add or propose tests for audit/event creation. | `application/audit.py`, `application/events.py`, tests | `tests/test_audit_events.py` exists and passes. |
| TOS-007 | Agent A | done | Review Discord/SSE/bot additions and confirm they do not own business logic. | `api/routers/discord.py`, `api/routers/sse.py`, `bot/` | Agent A refactored router; Agent B verified with `test_discord_boundary.py`. |
| TOS-008 | Agent A | ready for review | Clean runtime artifacts if they are not meant for Git. | logs, db files, screenshots, bot cache | Unstaged generated screenshots/log, ignored log/screenshots, removed bot `__pycache__`; bot uses env placeholders only. |

## Missing Test Checklist

Updated by Agent B on 2026-06-12 after inspecting all 8 test files (22 tests, all pass).

| Area | Existing Coverage | Missing / Risk | Priority |
| :--- | :--- | :--- | :--- |
| Score calculation | ✅ Placement points, penalty reason, bonus disabled, unknown placement | ❌ Kill points (if supported), bye points = 0, manual total override blocked | Medium |
| Tie-breaks | ✅ First-place count, average placement tested | ❌ Latest game points tie-break (#4), latest game placement (#5), admin decision (#6) | High |
| Rule validation / lock | ✅ Solo-only, top_n > lobby_size, valid MVP ruleset | ❌ Locked ruleset rejects normal edit, privileged correction with audit reason, preset mutation isolation | High |
| Registration duplicates | ✅ Full flow registers 16 unique players | ❌ Unit test for duplicate user, duplicate game_uid per-tournament, same UID different tournament | High |
| Capacity / waitlist | ❌ No dedicated test | ❌ Approve at full capacity → waitlist, concurrent final-slot overfill prevention, waitlist promotion audit | Critical |
| Check-in windows | ❌ No unit/service test | ❌ Check-in before open_time rejected, check-in after close_time rejected, duplicate check-in idempotent, ineligible player blocked, late override requires reason | High |
| Group generation | ✅ 16-player shape, 32-player shape, >64 rejected, approved-only flow | ❌ Regeneration before lock, movement after lock requires reason+audit | Medium |
| Score states | ✅ Final is terminal, score transitions tested in state_transitions | ❌ Draft→Submitted, Submitted→PendingVerification, Pending not in public leaderboard, correction audit | High |
| Disputes | ❌ No test | ❌ Player can dispute own score, cannot dispute other player, accepted dispute triggers correction, rejected needs reason, audit log | High |
| Public privacy | ✅ `contact_value`, `contact_method`, `review_note` excluded from public reg | ❌ Public leaderboard excludes Discord ID, private evidence URI, admin notes; stream-safe endpoint excludes same | High |
| Stream-safe endpoints | ❌ No test | ❌ `/public/leaderboard` only shows approved/final, `/sse/` stable under load, no private field leak | High |
| Audit / event outbox | ❌ No test | ❌ Rule lock creates event, registration approval creates event, score approval creates event, payloads exclude private fields | High |
| API errors | ❌ No test | ❌ Permission denied → 403, invalid state transition → 400, duplicate → 400 with current state | Medium |

## Update Log

### 2026-06-12 - Codex

Created this coordination file.

Reason:
The user wants one safe file where multiple AI agents can coordinate work, divide responsibilities, update progress, and discuss build/test flow without disrupting source code or core operating documents.

Next action:
Agent B should start with TOS-001 and TOS-002, then update the Task Board and Missing Test Checklist.

Risks:
The working tree currently has many active Tournament OS changes. Agents must avoid broad refactors or cleanup until the change set is reviewed.

---

### 2026-06-12 - Agent B

Task: TOS-001 (review staged changes) and TOS-002 (test coverage gap analysis)

Files read:
- `AGENT_COORDINATION.md`
- `SYSTEM_BOUNDARY.md`
- `docs/TEST_PLAN_PHASE_1.md`
- `tests/test_evidence.py`
- `tests/test_grouping.py`
- `tests/test_leaderboard.py`
- `tests/test_phase1_flow.py`
- `tests/test_rules.py`
- `tests/test_scoring.py`
- `tests/test_serializers.py`
- `tests/test_state_transitions.py`

Files changed:
- `AGENT_COORDINATION.md` (this file — task board and checklist updated)

Commands run:
```powershell
git -C e:\TTLIVE\projects status --short
cd e:\TTLIVE\projects\tournament-os\backend; python -m unittest discover -s tests -v
```

Result:
- **Git status:** 80+ files staged (A) or staged-with-working-tree-change (AM). Deleted files: `models/match.py` and `models/participant.py` (AD — staged delete). Two files have AM status indicating post-stage edits: `api/main.py`, `api/routers/discord.py`, `api/routers/registrations.py`, `api/routers/scores.py`, `application/registrations.py`, `application/rules.py`, `application/scoring.py`, `domain/enums.py`, `domain/scoring.py`, `models/__init__.py`, `models/base.py`, `models/tournament.py`, `web/routes.py`.
- **Unit tests:** 22 tests, all pass in 0.76s.
- **Test gap analysis:** See Missing Test Checklist above. 7 of 13 test areas have zero coverage. Critical gap is capacity/waitlist concurrency — no test exists.

Risks / blockers:

1. **`api/routers/discord.py` contains inline business logic** (User creation, Registration creation, approval, check-in session management). This violates the spec requirement that FastAPI service layer owns business logic. The router currently acts as a service. Agent A should move this to service layer or acknowledge as MVP tech debt before commit.
2. **Bot token (`DISCORD_TOKEN`) is visible in task run history** — must not be committed to Git. Confirm `.gitignore` covers `.env` and task log dirs.
3. **`tmp_screenshots/` is staged** — 3 PNG files. These appear to be local screenshots, not application assets. Recommend unstaging them (`git reset HEAD tournament-os/backend/tmp_screenshots/`).
4. **`migrations/` uses JSONB** — the Alembic migration fails on SQLite (JSONB unsupported). The current workaround is `Base.metadata.create_all()` in `main.py` lifespan. This is acceptable for SQLite dev but must not be used in production. TOS-004 should address migration strategy.
5. **AM files (post-stage edits)** — `main.py`, `discord.py`, and several core files have working-tree changes not yet staged. These changes include the lifespan auto-init fix, check-in session fix, and registration error handling improvements made this session. These must be staged before commit.

Next action:
- Agent A: Claim TOS-003 (serializer privacy), TOS-004 (migration safety), TOS-007 (discord.py logic boundary), TOS-008 (clean artifacts).
- Agent B: Will begin TOS-005 (write missing check-in, capacity, and score-state tests) and TOS-006 (audit/event tests) in next session.
- Stage AM files before commit: `git add tournament-os/backend/tournament_os/api/main.py tournament-os/backend/tournament_os/api/routers/discord.py` etc.
- Unstage `tmp_screenshots/`: `git reset HEAD tournament-os/backend/tmp_screenshots/`

### 2026-06-12 - Codex / Agent A

Task:
Started coordination with the second agent through this file.

Files read:

- `projects/tournament-os/AGENT_COORDINATION.md`
- current git status for `projects/tournament-os/backend/`

Files changed:

- `projects/tournament-os/AGENT_COORDINATION.md`

Commands run:

```powershell
Get-Content -Raw -Encoding UTF8 -LiteralPath 'E:\TTLIVE\projects\tournament-os\AGENT_COORDINATION.md'
git status --short -- 'projects/tournament-os/AGENT_COORDINATION.md' 'projects/tournament-os/backend'
```

Result:

- No update from Agent B was present yet.
- Agent A claimed TOS-003, TOS-004, and TOS-007.
- Agent B should start with TOS-001 and TOS-002, then update the Task Board and Missing Test Checklist.

Risks / blockers:

- The backend working tree has many staged, modified, and untracked files.
- Agent A will not edit backend source code until Agent B records the current risk review, unless the user explicitly asks for immediate implementation.

Next action:

- Agent B: inspect current backend change set and test coverage.
- Agent A: after Agent B posts findings, verify public serializers, migration/model alignment, and Discord/SSE/bot boundaries.

### 2026-06-12 - Agent B

Task: TOS-005 and TOS-006

Files read:
- `tournament_os/application/checkins.py`
- `tournament_os/application/registrations.py`
- `tournament_os/application/scoring.py`
- `tournament_os/application/events.py`

Files changed:
- `tests/test_checkins.py` (New)
- `tests/test_capacity.py` (New)
- `tests/test_score_lifecycle.py` (New)
- `tests/test_audit_events.py` (New)
- `AGENT_COORDINATION.md` (Updated)

Commands run:
```powershell
python -m unittest discover -s tests -v
```

Result:
- **TOS-005:** Added tests for check-ins, capacity, and score lifecycle. As expected from the code review, **3 tests currently fail** due to missing backend logic:
  1. `test_approve_at_full_capacity_moves_to_waitlist`: `CapacityTests` fails because the service currently approves registrations even when the tournament capacity is full.
  2. `test_check_in_before_open_time_rejected`: `CheckInTests` fails because the service does not validate `opens_at`.
  3. `test_check_in_after_close_time_rejected`: `CheckInTests` fails because the service does not validate `closes_at`.
- **TOS-006:** Added `test_audit_events.py`. These tests **pass successfully**, proving that registration approvals and score approvals correctly create `AuditLog` and `EventOutbox` records without leaking private data like `contact_value`.

Risks / blockers:
- Agent A needs to implement the missing business logic in `registrations.py` (capacity/waitlist) and `checkins.py` (time windows) to make the test suite pass.

Next action:
- Agent A should claim the implementation fixes for the failing tests, alongside TOS-003, TOS-004, TOS-007, and TOS-008.

### 2026-06-12 - Codex / Agent A

Task:
Responded to Agent B findings and executed TOS-003, TOS-004, TOS-007. Also fixed failures exposed by Agent B tests under TOS-005.

Files read:
- `projects/tournament-os/AGENT_COORDINATION.md`
- `projects/tournament-os/backend/tournament_os/api/routers/public.py`
- `projects/tournament-os/backend/tournament_os/domain/serializers.py`
- `projects/tournament-os/backend/tournament_os/api/routers/discord.py`
- `projects/tournament-os/backend/tournament_os/api/routers/sse.py`
- `projects/tournament-os/backend/tournament_os/application/registrations.py`
- `projects/tournament-os/backend/tournament_os/application/checkins.py`
- `projects/tournament-os/backend/tournament_os/application/scoring.py`
- `projects/tournament-os/backend/tournament_os/application/leaderboards.py`
- `projects/tournament-os/backend/tournament_os/models/competition.py`
- `projects/tournament-os/backend/tournament_os/models/overlay.py`
- `projects/tournament-os/backend/migrations/versions/20260612_0001_initial_phase_1_schema.py`
- Agent B tests: `test_capacity.py`, `test_checkins.py`, `test_score_lifecycle.py`

Files changed:
- `projects/tournament-os/backend/tournament_os/application/registrations.py`
- `projects/tournament-os/backend/tournament_os/application/checkins.py`
- `projects/tournament-os/backend/tournament_os/application/discord.py`
- `projects/tournament-os/backend/tournament_os/api/routers/discord.py`
- `projects/tournament-os/backend/migrations/versions/20260612_0001_initial_phase_1_schema.py`
- `projects/tournament-os/AGENT_COORDINATION.md`

Commands run:
```powershell
python -m unittest discover -s tests -v
rg "contact_value|contact_method|discord_id|evidence_uri|review_note|audit|formula_snapshot|payload_json" projects\tournament-os\backend\tournament_os\api projects\tournament-os\backend\tournament_os\web projects\tournament-os\backend\tournament_os\application projects\tournament-os\backend\tournament_os\domain
$env:TOURNAMENT_OS_DATABASE_URL='sqlite:///./tournament_os_smoke_agent_a.db'; python scripts\smoke_phase1.py --create-schema
Remove-Item -LiteralPath 'E:\TTLIVE\projects\tournament-os\backend\tournament_os_smoke_agent_a.db' -Force
```

Result:
- Agent B's new tests initially failed in 3 places:
  - capacity allowed approval beyond max participants
  - check-in before open time was accepted
  - check-in after close time was accepted
- Fixed capacity behavior: approving beyond `max_participants` now routes the registration to waitlist through `RegistrationService.waitlist_registration`, preserving audit/event behavior.
- Fixed check-in window behavior: `CheckInService.check_in` now rejects before `opens_at` and after `closes_at`.
- Refactored Discord API boundary:
  - Router now delegates to `DiscordIntegrationService`.
  - Removed mock leaderboard and mock score calculation from router.
  - Discord score submission now returns a domain error until it can submit via real backend round/group/score context.
- Added missing `overlay_configs` table to the initial Alembic migration so migration coverage matches the imported model.
- Unit tests now pass:

```text
Ran 33 tests
OK
```

- SQLite smoke passed end-to-end:
  - 16 registrations
  - group and check-in session generation
  - score approval
  - leaderboard
  - advancement
  - final assignment
  - winner calculation

Risks / blockers:
- PostgreSQL smoke without explicit SQLite URL is blocked locally by password authentication for user `tournament_os`.
- `tmp_screenshots/` is still staged; Agent A has not unstaged or deleted it because artifact intent should be confirmed.
- `uvicorn_debug.log` is still staged and likely should not be committed unless intentionally preserved.
- The new Discord service still contains MVP adapter behavior, but the router no longer owns the business logic. Score submission remains intentionally disabled instead of using fake scoring.
- `bot/` still needs a separate review for token handling and whether compiled `__pycache__` files should be ignored/removed.

Next action:
- Agent B: review Agent A changes and rerun tests.
- Agent B: add targeted tests for Discord boundary if desired: no mock leaderboard, score submit disabled, public payload excludes private fields.
- Agent A: after review, handle TOS-008 artifact cleanup if the user approves unstaging/removing runtime artifacts.

### 2026-06-12 - Agent B

Task: Review Agent A changes, rerun tests, and add Discord boundary tests.

Files read:
- `tournament_os/application/discord.py`

Files changed:
- `tests/test_discord_boundary.py` (New)
- `AGENT_COORDINATION.md` (Updated)

Commands run:
```powershell
python -m unittest discover -s tests -v
```

Result:
- **Test review:** Reran all 33 tests. They now pass successfully (33/33 OK). Agent A successfully implemented the missing logic for check-ins and capacity management.
- **Discord boundary tests:** Created `test_discord_boundary.py` to test the new `DiscordIntegrationService`. Tests confirm:
  1. `player_status` returns correct allowed actions and public info, without leaking `contact_value` or `contact_method`.
  2. `submit_score_from_discord` correctly raises a domain error as disabled.
  3. `leaderboard` returns actual empty arrays instead of mock data.
- **Task completion:** Marked TOS-003, TOS-004, TOS-005, TOS-006, and TOS-007 as `done` in the Task Board.

Risks / blockers:
- TOS-008 is the only remaining task. Artifact cleanup is needed before we can safely push this large set of changes to Git.

Next action:
- Let Agent A handle TOS-008 (artifact cleanup) if the user approves.
- Once TOS-008 is complete, the repository will be clean and ready for a commit covering the Phase 1 stability fixes.

### 2026-06-12 - Codex / Agent A

Task:
Continued Agent A work on TOS-008 and bot boundary cleanup.

Files read:
- `.gitignore`
- `projects/tournament-os/bot/main.py`
- `projects/tournament-os/bot/cogs/admin.py`
- `projects/tournament-os/bot/cogs/player.py`
- `projects/tournament-os/backend/tests/test_discord_boundary.py`

Files changed:
- `.gitignore`
- `projects/tournament-os/bot/cogs/admin.py`
- `projects/tournament-os/bot/cogs/player.py`
- `projects/tournament-os/AGENT_COORDINATION.md`

Commands run:
```powershell
rg -n "TOKEN|SECRET|PASSWORD|KEY|DISCORD|discord|Bearer|AIza|sk-|ghp_|xox" projects\tournament-os -S
python -m unittest discover -s tests -v
python -m compileall -q projects\tournament-os\bot
git reset HEAD -- projects/tournament-os/backend/tmp_screenshots projects/tournament-os/backend/uvicorn_debug.log
Remove-Item -LiteralPath 'E:\TTLIVE\projects\tournament-os\bot\cogs\__pycache__' -Recurse -Force
```

Result:
- Backend tests still pass:

```text
Ran 36 tests
OK
```

- Bot files compile successfully.
- No real secret value was found in bot source; `DISCORD_TOKEN` is read from env and fallback is the placeholder `YOUR_BOT_TOKEN_HERE`.
- `.gitignore` now ignores:
  - `*.log`
  - `projects/tournament-os/backend/tmp_screenshots/`
- Unstaged generated runtime artifacts:
  - `projects/tournament-os/backend/tmp_screenshots/`
  - `projects/tournament-os/backend/uvicorn_debug.log`
- Removed generated bot `__pycache__`.
- Bot boundary cleanup:
  - Admin leaderboard announcement now fetches backend `/discord/leaderboard` instead of hardcoded mock scores.
  - Admin group announcement no longer posts fake Group A/Group B data; it reports unavailable until a real backend announcement endpoint exists.
  - Admin check-in payload now includes configurable `TOURNAMENT_ID` and `TOURNAMENT_STAGE_ID`.
  - Player group and leaderboard views now read current backend payload fields.
  - Player error handling now reads the backend DomainError envelope when present.

Risks / blockers:
- `bot/` remains an early integration adapter and is not covered by runtime tests against Discord.
- `TOURNAMENT_STAGE_ID` defaults to `stage_1`, which is only a placeholder. Real deployments should set it from backend tournament setup.
- There are still many staged/uncommitted backend files from the broader active worktree; this update only cleaned generated artifacts and bot adapter issues.

Next action:
- Agent B should review TOS-008 and decide whether bot integration should remain in this commit or be separated into a later commit.
- If preparing a commit, stage the newly modified files intentionally and keep generated artifacts out of the index.

## Agent Update Template

Copy this block when posting a new update:

```markdown
### YYYY-MM-DD - Agent Name

Task:

Files read:

Files changed:

Commands run:

Result:

Risks / blockers:

Next action:
```
