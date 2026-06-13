# Tournament OS Backend

Phase 1 backend foundation for Tournament Operating System.

Current implementation focus:

- domain enums shared by API, database, and tests
- backend-owned score calculation
- leaderboard ranking from approved/final scores
- public-safe serializers that exclude private registration data

The first tests are intentionally domain-only so the rules can be verified before PostgreSQL and API routes are wired in.

## Run Tests

From repository root:

```powershell
python -m unittest discover -s projects\tournament-os\backend\tests
```

## Local PostgreSQL

If Docker is available:

```powershell
Set-Location projects\tournament-os\backend
docker compose up -d postgres
alembic upgrade head
python scripts\smoke_phase1.py
python -m uvicorn tournament_os.api.main:app --host 127.0.0.1 --port 8010
```

If PostgreSQL is installed another way, set:

```powershell
$env:TOURNAMENT_OS_DATABASE_URL="postgresql+psycopg://user:password@localhost:5433/tournament_os"
```

For a quick local smoke run without PostgreSQL:

```powershell
$env:TOURNAMENT_OS_DATABASE_URL="sqlite:///./tournament_os_smoke.db"
python scripts\smoke_phase1.py --create-schema
```

## Demo Web Pages

After creating a smoke database and starting the server with the same database URL:

```powershell
$env:TOURNAMENT_OS_DATABASE_URL="sqlite:///./tournament_os_demo.db"
python -m uvicorn tournament_os.api.main:app --host 127.0.0.1 --port 8010
```

Open:

- `http://127.0.0.1:8010/`
- `http://127.0.0.1:8010/web/tournaments/{public_slug}`
- `http://127.0.0.1:8010/web/tournaments/{public_slug}/stream`

## Planned Layers

```text
tournament_os/
  api/
  application/
  domain/
  models/
  repositories/
  schemas/
```

