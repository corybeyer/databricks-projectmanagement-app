---
name: status
description: Show current project status — git branch, uncommitted changes, current phase/sprint from CLAUDE.md, and what to work on next.
---

Show the current state of PM Hub development.

## Steps

1. Read CLAUDE.md to get:
   - Current Phase
   - Current Sprint (if applicable)
   - Current Focus
   - Blockers
   - Next Gate

2. Run git commands to get:
   - Current branch: `git branch --show-current`
   - Uncommitted changes: `git status --short`
   - Recent commits: `git log --oneline -5`
   - Branches: `git branch -a`

3. Check for potential issues:
   - Are you on `main` or `develop` directly? (Should be on a feature branch)
   - Are there uncommitted changes? (Should commit or stash)
   - Is the branch up to date with develop? `git log develop..HEAD --oneline`

4. Present a clean status report:

```
═══ PM Hub Status ═══

Project Phase:  Phase 1 — Planning & Design
Sprint:         N/A (sprints begin Phase 3)
Focus:          Schema finalization
Next Gate:      Gate 1 — Charter Approved

Branch:         feature/risk-register
Base:           develop (3 commits ahead)
Uncommitted:    2 files modified

Recent commits:
  abc1234 feat: add risk register table component
  def5678 feat: add probability-impact heatmap

Suggestion:     You have uncommitted changes. Run /commit to save your work.
```

5. If there are things to flag, add suggestions:
   - "You're on develop directly — create a feature branch with /branch"
   - "Your branch is 10+ commits ahead — consider creating a PR with /pr"
   - "CLAUDE.md shows a blocker — address it before continuing"
