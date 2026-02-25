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

### Databricks Documentation
Good candidates to add:
- Databricks Apps deployment guide
- Unity Catalog best practices
- SQL statement execution API reference
- Databricks SDK Python reference
- Security best practices for Databricks Apps

## Current Reference Files

| File | Contents |
|------|----------|
| `databricks-sdk-patterns.md` | WorkspaceClient, OBO auth, result handling |
| `parameterized-queries.md` | F-string → parameterized SQL migration guide |
| `deployment-config.md` | app.yaml, requirements.txt, .gitignore rules |
| `apps-cookbook.md` | Pre-fetched patterns from apps-cookbook.dev |

## Tips
- Keep files under 20 pages / ~50KB for best agent performance
- Use `.md` format when possible (faster to parse than PDF)
- The agent reads ALL files in this directory, so remove outdated materials
