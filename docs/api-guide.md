# DevMind AI: REST API Guide

All REST endpoints are versioned under `/api/v1` and documented interactively via OpenAPI at `http://localhost:8088/docs`.

## Endpoint Reference

### Workspaces
- `GET /api/v1/workspaces/` — List all workspaces
- `POST /api/v1/workspaces/` — Create new workspace (`name`, `description`)
- `GET /api/v1/workspaces/{id}` — Fetch workspace details

### Repositories
- `POST /api/v1/repositories/import-git` — Ingest repository via public Git URL
- `POST /api/v1/repositories/upload-zip` — Ingest repository via ZIP upload
- `GET /api/v1/repositories/?workspace_id=...` — List repositories
- `GET /api/v1/repositories/{id}` — Fetch repository summary and active revision
- `DELETE /api/v1/repositories/{id}` — Delete repository and purge local files

### Analysis Jobs
- `POST /api/v1/analysis/jobs/{repo_id}` — Trigger 7-stage background analysis pipeline
- `GET /api/v1/analysis/jobs/{job_id}` — Check status, progress percentage, and stage logs
- `GET /api/v1/analysis/jobs/repo/{repo_id}` — Fetch latest job for repository

### Code & Symbols
- `GET /api/v1/code/files/{revision_id}` — List source files with LOC and layer metadata
- `GET /api/v1/code/tree/{revision_id}` — Hierarchical directory tree
- `GET /api/v1/code/file-content/{revision_id}?path=...` — Fetch source code and symbols
- `GET /api/v1/code/symbols/{revision_id}` — Filter discovered symbols

### Dependency Graph
- `GET /api/v1/graph/{revision_id}?node_type=file&relationship=all` — React Flow graph nodes, edges, cycle detection, and centrality scores

### Code Search
- `POST /api/v1/search/{revision_id}` — Unified code search (`query`, `search_type`: symbol, file, fulltext, regex)

### AI Assistant
- `POST /api/v1/ai/{revision_id}/ask` — Grounded Q&A with verified citation badges `[file:start-end]`
- `GET /api/v1/ai/{revision_id}/conversations` — Fetch chat history

### Change Impact
- `POST /api/v1/impact/{revision_id}/analyze` — Blast radius calculation (`symbol_id`, `symbol_name`, `file_path`, `depth`)

### Security & Quality
- `GET /api/v1/security/{revision_id}/findings` — Static analysis findings from Ruff and Bandit
- `PATCH /api/v1/security/findings/{id}/dismiss` — Toggle false-positive status

### Revision Comparison
- `POST /api/v1/compare/revisions` — Diff two revisions (`base_revision_id`, `target_revision_id`)

### Architecture Reports
- `GET /api/v1/reports/{revision_id}/architecture` — Exportable Markdown architecture report
