# Adding Reference Materials to the Databricks Review Agent

This directory (`review-databricks/ref/`) is pre-loaded by the review agent at the start of every review. Drop your reference materials here and they'll automatically be used.

## How to Add Materials

### Web Pages
1. Fetch the content and save as markdown:
   ```
   Use Claude: "Fetch https://example.com/docs and save to .claude/skills/review-databricks/ref/filename.md"
   ```
2. Or manually copy-paste content into a `.md` file

### PDF Documents
1. Drop PDF files directly into this directory
2. The agent reads PDFs with the Read tool (max 20 pages per call)
3. Name them descriptively: `databricks-sdk-migration-guide.pdf`

## Current Reference Files

| File | Source | Contents |
|------|--------|----------|
| `databricks-apps-auth.md` | [MS Learn — Configure authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth) | Two auth models (app vs user), OBO setup, scopes, headers, combining models |
| `databricks-apps-platform.md` | [MS Learn — Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/) | Runtime env, pre-installed libs, app.yaml, resources, best practices |
| `databricks-sdk-patterns.md` | Custom | Approved OBO connection pattern, anti-patterns, error handling |
| `parameterized-queries.md` | Custom | F-string → parameterized SQL migration guide |
| `deployment-config.md` | Custom | app.yaml rules, requirements.txt pinning, .gitignore |
| `apps-cookbook.md` | [apps-cookbook.dev](https://apps-cookbook.dev) | Cookbook patterns annotated with PM Hub applicability |

## Microsoft Learn Pages — Coverage Status

Covered (distilled into ref docs above):
- [x] Overview / index page
- [x] Key concepts
- [x] Configure authorization (auth)
- [x] HTTP headers
- [x] App runtime (app.yaml)
- [x] Environment variables
- [x] System environment (pre-installed packages)
- [x] Best practices
- [x] App development overview
- [x] Resources

Not yet covered (fetch on-demand via MCP tools during development):
- [ ] Deploy apps
- [ ] Monitor apps
- [ ] Embed apps
- [ ] Configure networking
- [ ] Configure permissions
- [ ] Configure compute size
- [ ] Manage dependencies
- [ ] Create app from template / custom

## Tips
- Keep files under 20 pages / ~50KB for best agent performance
- Use `.md` format when possible (faster to parse than PDF)
- The agent reads ALL files in this directory, so remove outdated materials
- For pages not yet covered, use the Microsoft Learn MCP tools during development:
  `microsoft_docs_search` for quick lookups, `microsoft_docs_fetch` for full pages
