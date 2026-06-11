# Tournament Format Specification

Initial target: Golden Spatula weekly tournament.

The first version should support a group-based format with cumulative points because this matches score-based games better than a complex bracket-first system.

## MVP Format

Name: Golden Weekly

Participant type: Solo player

Default capacity:

- 64 players

Default stage structure:

```text
Round 1
  8 groups
  8 players per group
  Top 4 advance

Round 2
  4 groups
  8 players per group
  Top 4 advance

Final
  16 players
```

This format is a starting assumption and must be reviewed before real use.

## Configurable Fields

- Maximum players
- Players per group
- Number of rounds
- Advancement count per group
- Placement points
- Bonus point categories
- Penalty categories
- Bye behavior
- Tie-break order

## Score Formula

The exact Golden Spatula score formula is not locked yet. The current recommended draft is maintained in `COMPETITION_RULES_DRAFT.md`.

Current draft placeholder:

| Result | Points |
| :--- | ---: |
| 1st place | 10 |
| 2nd place | 8 |
| 3rd place | 7 |
| 4th place | 6 |
| 5th place | 4 |
| 6th place | 3 |
| 7th place | 2 |
| 8th place | 1 |
| Bonus point | Configurable |
| Penalty | Configurable |
| Bye | Configurable |

## Tie-Break Rules

Tie-break rules are not final.

Recommended starting order:

1. Higher total score
2. Higher best single-round placement
3. Higher latest-round score
4. Lower penalty total
5. Admin decision with audit note

## Bye Rules

Supported bye behaviors:

- Advance only
- Fixed bye points
- Average points from previous completed rounds

MVP recommendation:

- Use fixed bye points only if the tournament rules announce it before registration closes.
- Otherwise use advance-only bye to avoid score disputes.

## Public Result Rules

- Show approved scores by default.
- Mark pending scores as pending if public pending visibility is enabled.
- Never show phone number, Line ID, Discord ID, or private evidence links publicly.
