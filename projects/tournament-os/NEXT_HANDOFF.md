# Next Handoff

Use this file when continuing the system in Codex, Cursor, Claude Code, or another development environment.

## First Prompt

```text
Read AGENTS.md.
Read projects/tournament-os/README.md.
Read projects/tournament-os/SYSTEM_BOUNDARY.md.
Read projects/tournament-os/PROJECT_CONTEXT.md.
Read all files under projects/tournament-os/spec/.
Read projects/tournament-os/docs/DOCUMENTATION_SUITE.md to understand the full documentation map and missing documents.
Pay special attention to projects/tournament-os/spec/SYSTEM_REQUIREMENTS_SPECIFICATION.md as the Phase 1 system requirements review document.
Pay special attention to projects/tournament-os/spec/MVP_RULESET.md as the current proposed MVP baseline.
Pay special attention to projects/tournament-os/spec/GROUP_POINTS_QUALIFIER_SPEC.md as the Phase 1 scoring and advancement contract.
Pay special attention to projects/tournament-os/spec/ENUMS_AND_STATES.md as the shared backend vocabulary.
Pay special attention to projects/tournament-os/spec/RULE_CONFIG_EXAMPLES.md as the first rule configuration contract.
Pay special attention to projects/tournament-os/spec/ER_DIAGRAM.md as the current relationship map.
Pay special attention to projects/tournament-os/spec/CHECK_IN_SPEC.md because check-in is per session/stage/day, not one tournament-wide status.
Pay special attention to projects/tournament-os/spec/RULESET_SELECTION_AND_CREATION_UI.md because tournament creation must include ruleset selection and validation.
Pay special attention to projects/tournament-os/spec/IMPLEMENTATION_SCHEMA_PLAN.md as the Phase 1 PostgreSQL schema plan.
Pay special attention to projects/tournament-os/spec/API_CONTRACT_PHASE_1.md as the first FastAPI contract.
Pay special attention to projects/tournament-os/spec/PHASE_1_IMPLEMENTATION_DECISIONS.md because it locks the recommended Phase 1 scope.
Pay special attention to projects/tournament-os/spec/RULE_ENGINE_SPEC.md because rules must be configurable and affect score calculation.
Read projects/tournament-os/docs/SPEC_GAP_ANALYSIS.md for the current readiness assessment.
Read projects/tournament-os/docs/SYSTEM_ARCHITECTURE_DESIGN.md before implementing backend modules.
Read projects/tournament-os/docs/TEST_PLAN_PHASE_1.md before writing tests or accepting Phase 1.
Read projects/tournament-os/docs/WEB_APP_DESIGN_AND_INTEGRATION_SPEC.md before planning frontend, realtime, Discord, bot, or overlay work.
Read projects/tournament-os/docs/DISCORD_OPERATIONS_AND_PLUGIN_SPEC.md before planning Discord bot commands, notification delivery, or plugin processing.
Read projects/tournament-os/docs/BOT_WEB_FLOW_AND_DATA_SPEC.md before implementing Discord buttons, player messages, read models, or dashboard synchronization.
Read projects/tournament-os/docs/POSTGRES_MODULE_FLOW_ANALYSIS.md before finalizing PostgreSQL schema, service modules, read models, or event/outbox design.
Read projects/tournament-os/docs/EVIDENCE_AND_DISCORD_ROLE_ANALYSIS.md before implementing image evidence, OCR/plugin helpers, Discord role assignment, or bot permission checks.
Read projects/tournament-os/backlog/GITHUB_ISSUES_PHASE_1.md before creating GitHub Issues.
Read projects/tournament-os/backlog/GITHUB_ISSUE_UPDATE_2026-06-12.md before posting the first Tournament OS GitHub update comment.
Read projects/tournament-os/tools/README.md before creating GitHub Issues by script.

Summarize your understanding of Tournament Operating System.
Do not write code yet.

List:
- Missing specifications
- Risks
- Database entities
- FastAPI services
- Web app surfaces
- Realtime and Discord integration boundaries
- Discord operations and plugin processing plan
- Bot/web end-to-end flow and data read model
- PostgreSQL module flow and schema improvement analysis
- Evidence image and Discord role permission analysis
- Phase 1 implementation schema and API contract
- System requirements coverage
- Development plan
- Documentation suite status
```

## Before Writing Code

Confirm these decisions:

- Confirm Golden Spatula is still the first tournament game.
- Confirm MVP is solo-only.
- Confirm first real event size is 16 or 32 players.
- Confirm placement score formula: 10/8/7/6/4/3/2/1.
- Confirm first supported tournament models: Fixed Points and Group Points Qualifier.
- Confirm Create Tournament flow includes ruleset/preset selection.
- Confirm tie-break order in `spec/MVP_RULESET.md`.
- Confirm default bye behavior is advance-only.
- Confirm check-in is manual or stored status only.
- Confirm check-in sessions are generated per stage/day.
- Confirm 2 games per qualifier stage and 3 games in final.
- Confirm scores reset each stage.
- Confirm Score Admin or Referee can approve scores.
- Confirm Tournament Admin or Referee can resolve disputes.
- Confirm Excel export before PDF.

## Recommended Build Order

1. Review specifications.
2. Confirm MVP decisions in `spec/MVP_RULESET.md`.
3. Finalize PostgreSQL schema from `spec/ER_DIAGRAM.md` and `spec/DATABASE_SCHEMA.md`.
4. Define API request/response schemas.
5. Create FastAPI backend skeleton.
6. Create SQLAlchemy models.
7. Create Alembic migrations.
8. Implement registration service.
9. Implement tournament setup service.
10. Implement rule set validation service.
11. Implement score calculation service.
12. Implement leaderboard service.
13. Implement audit log service.
14. Add tests.
15. Add admin workflow.
16. Add public leaderboard.
17. Add Discord, OCR, and overlay integrations later.

## Do Not Build Yet

- Payment
- Mobile app
- SaaS multi-tenant platform
- Full Discord bot
- Full OCR automation
- Complex OBS control
