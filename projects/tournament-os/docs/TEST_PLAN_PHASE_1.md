# Test Plan Phase 1

Project: Tournament Operating System  
Status: Phase 1 test plan draft

## Purpose

Define the minimum tests required before Tournament OS Phase 1 is considered safe for real tournament use.

Tests should prove business correctness, privacy, concurrency safety, and stream-safe public display.

## Test Areas

### 1. Ruleset And Tournament Setup

- Create tournament draft with valid required fields.
- Reject opening registration before ruleset is valid.
- Copy preset into tournament-specific draft ruleset.
- Verify editing draft ruleset does not mutate preset.
- Lock ruleset and score formula snapshot.
- Reject normal edits after lock.
- Allow privileged correction only with audit reason.

### 2. Registration

- Player can submit one registration per tournament.
- Duplicate user registration returns duplicate/current state.
- Duplicate game UID in same tournament is rejected.
- Same game UID in different tournament can be allowed if rules permit.
- Rejected/waitlisted/withdrawn registrations are not grouped.
- Public registration response excludes contact value.

### 3. Registration Capacity And Waitlist

- Approving player when capacity remains succeeds.
- Approving player when capacity is full moves to waitlist or rejects by policy.
- Two admin approvals at final capacity cannot overfill tournament.
- Waitlist promotion is transactional and audited.

### 4. Check-In

- Check-in opens at configured open time.
- Check-in before open time is rejected.
- Check-in after close time is rejected unless admin override.
- Duplicate check-in returns current state.
- Ineligible player cannot check in.
- Late override requires reason and audit log.
- No-show and replacement state is recorded.

### 5. Group Generation

- Only approved players are grouped.
- 16-player Group Points Qualifier generates 2 lobbies of 8 and final structure.
- 32-player Group Points Qualifier generates Round 1, Semi Final, and Final.
- Regeneration before lock follows policy.
- Movement after lock requires reason and audit log.

### 6. Score Calculation

- Placement points calculate from locked formula: 10/8/7/6/4/3/2/1.
- Scoring service does not hardcode default points except seed/preset creation.
- Duplicate placements in one game are rejected.
- Missing placement is rejected or kept draft by policy.
- Penalty greater than 0 requires reason.
- Bonus points default to 0.
- Bye points default to 0.
- Manual total override is unavailable in normal flow.

### 7. Score States

- Score can move Draft -> Submitted.
- Submitted score can move Pending Verification.
- Approved score affects leaderboard.
- Pending score does not affect public leaderboard by default.
- Final score cannot be edited by normal flow.
- Correction requires authorized actor, reason, audit log, and leaderboard rebuild.

### 8. Leaderboard And Advancement

- Leaderboard sums approved/final scores only.
- Tie-break order is applied:
  1. total points
  2. first-place count
  3. average placement
  4. latest game points
  5. latest game placement
  6. admin decision
- Top 4 per lobby advance by default.
- Scores reset each stage by default.
- Final stage rank 1 becomes winner.
- Admin tie-break decision requires reason and audit log.

### 9. Disputes

- Player can dispute own score within dispute window.
- Player cannot dispute other player's private data.
- Dispute can move under review.
- Accepted dispute triggers score correction.
- Rejected dispute requires reason.
- Dispute resolution creates audit log.

### 10. Public And Stream-Safe Data

- Public leaderboard excludes contact data.
- Public leaderboard excludes Discord ID unless explicitly public.
- Public leaderboard excludes private evidence.
- Public leaderboard excludes admin notes and audit payloads.
- Stream-safe leaderboard uses approved/final scores by default.
- Stream-safe groups endpoint excludes private fields.
- OBS/TikTok Live Studio endpoint returns stable response under MVP scale.

### 11. Event Outbox And Audit

- Rule lock creates audit/event.
- Registration approval creates audit/event.
- Group generation creates audit/event.
- Check-in override creates audit/event.
- Score approval creates audit/event.
- Dispute acceptance creates audit/event.
- Export creates audit/event.
- Event payloads do not leak private contact or evidence.

### 12. API Error Behavior

- Permission denied returns clear error.
- Invalid state transition returns clear error.
- Duplicate submission returns current state when appropriate.
- Public endpoints use public-safe serializer.
- Admin endpoints require authentication/authorization.

## Minimum Automated Test Set

Before backend Phase 1 is accepted:

- unit tests for score calculation
- unit tests for tie-breaks
- unit tests for rule validation
- service tests for registration duplicate constraints
- service tests for check-in windows
- service tests for score approval
- service tests for dispute correction
- integration tests for public/private serializers
- integration tests for stream-safe endpoints
- transaction/concurrency tests for capacity, check-in, and score approval

## Manual Smoke Test

Run a full 16-player event simulation:

1. create tournament
2. select Group Points Qualifier
3. lock rules
4. register 16 players
5. approve players
6. generate groups
7. open check-in
8. check in players
9. enter two games per lobby
10. approve scores
11. verify Round 1 Top 4 per lobby
12. generate final
13. enter three final games
14. approve scores
15. verify winner
16. verify public leaderboard
17. verify stream-safe leaderboard
18. export Excel

## Exit Criteria

Phase 1 backend is not ready for real tournament use until:

- score calculation tests pass
- rule lock tests pass
- public privacy tests pass
- check-in tests pass
- advancement tests pass
- dispute correction tests pass
- stream-safe endpoint tests pass
- audit/event tests pass
