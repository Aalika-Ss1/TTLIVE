# Tournament Operating System

Tournament Operating System is the planned web system for running game competitions from registration to final results.

This is a separate subsystem added for tournament cases. It is intentionally isolated from the normal TTLIVE weekly live workflow so it can later become a real application or its own repository.

System boundary: `SYSTEM_BOUNDARY.md`

Next development handoff: `NEXT_HANDOFF.md`

The system should help a solo organizer or small team manage:

- Player or team registration
- Admin approval
- Tournament setup
- Group and bracket generation
- Per-round score entry
- Automatic point totals
- Public leaderboards
- Score verification and disputes
- Exportable results

Current phase: specification.

Do not start full application development until the core rules in `spec/BUSINESS_RULES.md`, `spec/STATE_MACHINE.md`, and `spec/TOURNAMENT_FORMAT_SPECIFICATION.md` are reviewed.

## Suggested Reading Order

1. `SYSTEM_BOUNDARY.md`
2. `PROJECT_CONTEXT.md`
3. `spec/BUSINESS_RULES.md`
4. `spec/STATE_MACHINE.md`
5. `spec/COMPETITION_RULES_DRAFT.md`
6. `spec/TOURNAMENT_FORMAT_SPECIFICATION.md`
7. `spec/DATABASE_SCHEMA.md`
8. `spec/API_SPECIFICATION.md`
9. `docs/DEVELOPMENT_ROADMAP.md`
10. `backlog/PHASE_1.md`
11. `NEXT_HANDOFF.md`

## MVP Scope

- Register players or teams
- Approve or reject registrations
- Create one tournament
- Divide participants into groups
- Record scores per round
- Calculate total score automatically
- Publish leaderboard
- Export results to Excel or PDF

## Not In Scope Yet

- Payment
- Mobile app
- SaaS multi-tenant platform
- Complex sponsor workflow
- Full Discord bot automation
- Full OCR automation
- Advanced OBS overlay control
