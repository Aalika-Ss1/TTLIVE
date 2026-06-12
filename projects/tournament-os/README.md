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

Do not start full application development until the core rules in `spec/MVP_RULESET.md`, `spec/ENUMS_AND_STATES.md`, `spec/RULE_CONFIG_EXAMPLES.md`, `spec/ER_DIAGRAM.md`, `spec/BUSINESS_RULES.md`, `spec/STATE_MACHINE.md`, and `spec/TOURNAMENT_FORMAT_SPECIFICATION.md` are reviewed.

## Suggested Reading Order

1. `SYSTEM_BOUNDARY.md`
2. `PROJECT_CONTEXT.md`
3. `docs/DOCUMENTATION_SUITE.md`
4. `spec/SYSTEM_REQUIREMENTS_SPECIFICATION.md`
5. `spec/MVP_RULESET.md`
6. `spec/GROUP_POINTS_QUALIFIER_SPEC.md`
7. `spec/ENUMS_AND_STATES.md`
8. `spec/RULE_CONFIG_EXAMPLES.md`
9. `spec/ER_DIAGRAM.md`
10. `spec/CHECK_IN_SPEC.md`
11. `spec/RULESET_SELECTION_AND_CREATION_UI.md`
12. `spec/IMPLEMENTATION_SCHEMA_PLAN.md`
13. `spec/API_CONTRACT_PHASE_1.md`
14. `spec/PHASE_1_IMPLEMENTATION_DECISIONS.md`
15. `spec/BUSINESS_RULES.md`
16. `spec/STATE_MACHINE.md`
17. `spec/COMPETITION_RULES_DRAFT.md`
18. `spec/RULE_ENGINE_SPEC.md`
19. `spec/TOURNAMENT_FORMAT_SPECIFICATION.md`
20. `spec/DATABASE_SCHEMA.md`
21. `spec/API_SPECIFICATION.md`
22. `docs/SPEC_GAP_ANALYSIS.md`
23. `docs/SYSTEM_ARCHITECTURE_DESIGN.md`
24. `docs/TEST_PLAN_PHASE_1.md`
25. `docs/WEB_APP_DESIGN_AND_INTEGRATION_SPEC.md`
26. `docs/DISCORD_OPERATIONS_AND_PLUGIN_SPEC.md`
27. `docs/BOT_WEB_FLOW_AND_DATA_SPEC.md`
28. `docs/POSTGRES_MODULE_FLOW_ANALYSIS.md`
29. `docs/EVIDENCE_AND_DISCORD_ROLE_ANALYSIS.md`
30. `docs/DEVELOPMENT_ROADMAP.md`
31. `backlog/PHASE_1.md`
32. `backlog/GITHUB_ISSUES_PHASE_1.md`
33. `backlog/GITHUB_ISSUE_UPDATE_2026-06-12.md`
34. `tools/README.md`
35. `NEXT_HANDOFF.md`

## MVP Scope

- Register solo players
- Approve or reject registrations
- Create one tournament
- Divide participants into groups
- Record scores per round
- Calculate total score automatically
- Publish leaderboard
- Export results to Excel first

## Not In Scope Yet

- Payment
- Mobile app
- SaaS multi-tenant platform
- Complex sponsor workflow
- Required team registration
- Full Discord bot automation
- Full OCR automation
- Advanced OBS overlay control
