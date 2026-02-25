---
name: commit
description: Stage changes and create a conventional commit message. Analyzes what changed, determines the correct commit type, and writes a properly formatted message.
arguments:
  - name: message
    description: "Optional: override message. If omitted, Claude analyzes the diff and generates one."
    required: false
---

Create a conventional commit following PM Hub standards.

## Steps

1. Run `git status` and `git diff --staged` (or `git diff` if nothing staged) to see what changed.
2. Analyze the changes to determine:
   - **What files changed** — pages/, utils/, models/, assets/, etc.
   - **What type of change** — new feature, bug fix, schema, style, docs, etc.
   - **What the change does** — read the actual diff
3. Determine the commit type based on what changed:
   - Changes in `pages/` with new functionality → `feat`
   - Changes in `models/` or `.sql` files → `schema`
   - Changes in `assets/` or CSS → `style`
   - Changes in `*.md` or docs → `docs`
   - Bug fixes (look for fix-related changes) → `fix`
   - Restructuring without behavior change → `refactor`
   - Test files → `test`
   - CI/CD, app.yaml → `deploy`
   - requirements.txt, cleanup → `chore`
4. If the user provided a message, validate it follows convention and use it.
5. If no message provided, generate one:
   - Imperative mood ("add" not "added")
   - Lowercase
   - Under 50 characters
   - No period at the end
6. If changes span multiple concerns, write a multi-line commit:
   ```
   type: short summary
   
   - Detail 1
   - Detail 2
   ```
7. Stage all changes (if not already staged) and commit:
   ```bash
   git add .
   git commit -m "type: generated message"
   ```
8. Show the commit log entry to confirm.

## Validation

- Message must start with a valid type followed by colon and space
- Description must be imperative mood, lowercase, no period
- Total first line under 50 characters
- If user provides invalid format, fix it and explain why

## Example Outputs

```
feat: add portfolio health donut chart
schema: create gates table for phase approvals  
fix: handle null assignee in kanban card render
refactor: move chart theme constants to shared config
style: darken kanban column headers
docs: add deployment steps to README
```
