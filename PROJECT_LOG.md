# Retail Profitability Diagnostic — Project Log

## Status
| Phase | Name | Status | Started | Signed off |
|---|---|---|---|---|
| 0 | Charter & environment lock | COMPLETE | | |
| 1 | Data audit & cleaning | Phase 1A COMPLETE| | |
| | |Phase 1B-i COMPLETE| | |
| | |Phase 1B-ii IN PROGRESS| | |
| 2 | SQL analytical layer | NOT STARTED | | |
| 3 | Diagnostic notebook | NOT STARTED | | |
| 4 | Dashboard | NOT STARTED | | |
| 5 | Memo & packaging | NOT STARTED | | |
| 6 | Quality gate & rehearsal | NOT STARTED | | |

## Decision log
| Date | Decision | Reason |
|---|---|---|
| 2026-10-29 | Validation script CHK4/CHK6 reference fact_line_items.gross_profit, which does not exist. Fact column is named contribution_margin (locked assumption #5). Fixed by pointing CHK4/CHK6 at contribution_margin. | Schema/validation naming mismatch — caught by validation layer before any downstream artifact depended on it. |

## Blocker log
| Date | Blocker | Resolved |
|---|---|---|