# Next Handoff

Use this file when continuing the system in Codex, Cursor, Claude Code, or another development environment.

## First Prompt

```text
Read AGENTS.md.
Read projects/tournament-os/README.md.
Read projects/tournament-os/SYSTEM_BOUNDARY.md.
Read projects/tournament-os/PROJECT_CONTEXT.md.
Read all files under projects/tournament-os/spec/.
Pay special attention to projects/tournament-os/spec/COMPETITION_RULES_DRAFT.md as the current proposed tournament rule draft.

Summarize your understanding of Tournament Operating System.
Do not write code yet.

List:
- Missing specifications
- Risks
- Database entities
- FastAPI services
- Development plan
```

## Before Writing Code

Confirm these decisions:

- First tournament game
- Solo or team registration for MVP
- Maximum players for first event
- Score formula
- Tie-break rules
- Bye rules
- Check-in rules
- Number of games per round
- Whether scores reset each round or carry forward
- Who can approve scores
- Who can resolve disputes
- Export format priority

## Recommended Build Order

1. Review specifications.
2. Generate ER diagram.
3. Finalize PostgreSQL schema.
4. Create FastAPI backend skeleton.
5. Create SQLAlchemy models.
6. Create Alembic migrations.
7. Implement registration service.
8. Implement tournament setup service.
9. Implement score calculation service.
10. Implement leaderboard service.
11. Implement audit log service.
12. Add tests.
13. Add admin workflow.
14. Add public leaderboard.
15. Add Discord, OCR, and overlay integrations later.

## Do Not Build Yet

- Payment
- Mobile app
- SaaS multi-tenant platform
- Full Discord bot
- Full OCR automation
- Complex OBS control
