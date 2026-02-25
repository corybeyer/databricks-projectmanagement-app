---
description: Run all review agents and produce a consolidated quality report
allowed-tools: Bash(git *), Bash(ruff *)
---

Run all three review agents and produce a consolidated quality report.

## Steps

1. Run the three reviews in sequence:
   - `/review-databricks`
   - `/review-security`
   - `/review-architecture`

2. After all three complete, produce a **consolidated summary**:

```
# Code Review — PM Hub (Consolidated)

## Overall Risk Level: CRITICAL | HIGH | MEDIUM | LOW

> The overall risk level is the HIGHEST severity found across all agents.

## Summary Table
| Agent | Risk Level | Critical | High | Medium | Low |
|-------|-----------|----------|------|--------|-----|
| Databricks | ... | ... | ... | ... | ... |
| Security | ... | ... | ... | ... | ... |
| Architecture | ... | ... | ... | ... | ... |
| **Total** | **...** | **...** | **...** | **...** | **...** |

## Critical Findings (Merge Blockers)
> List ALL critical findings from all agents here. These BLOCK merge.

## High Findings (Should Fix)
> List ALL high findings. Strongly recommended before merge.

## Action Items
1. [ ] Fix: <critical item 1>
2. [ ] Fix: <critical item 2>
3. [ ] Consider: <high item 1>

## Verdict
- **BLOCK**: If any CRITICAL findings exist — Do not merge
- **WARN**: If only HIGH findings — Merge with caution
- **PASS**: If only MEDIUM/LOW — Safe to merge
```

3. Present the verdict clearly to the user.

## Important Notes
- If any agent encounters an error, note it in the summary but continue with remaining agents
- The consolidated risk level is always the HIGHEST across all agents
- CRITICAL findings = merge blockers (used by `/merge-pr` to gate merges)
