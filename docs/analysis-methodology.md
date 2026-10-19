# DevMind AI: Analysis Methodology & Static Program Analysis

## Analysis Pipeline Stages

### Stage 1: Discovery & Inventory
- Traverses the repository directory tree safely, excluding noisy folders (`.git`, `node_modules`, `.venv`, `dist`, `build`, caches).
- Measures lines of code (LOC), file sizes, and extensions.
- Detects frameworks (FastAPI, React, Django, Flask, Express, Next.js, Pytest) using directory signatures and configuration files.
- Identifies candidate entry points (`main.py`, `app.py`, `index.ts`, `main.tsx`).

### Stage 2: Dual-Engine Parsing
- **Python**: Tree-sitter Python combined with Python's standard `ast` module. Extracts functions, decorators, parameters, type annotations, return types, classes, inheritance bases, imports (relative and absolute), docstrings, and function calls.
- **TypeScript & TSX**: Tree-sitter TypeScript and TSX grammars. Extracts interfaces, type aliases, classes, methods, arrow functions, ES module imports, and exports.

### Stage 3: Symbol Indexing & Architectural Layering
- Every symbol is assigned a stable unique identifier and associated with its source file and exact line range (`start_line`, `end_line`).
- Architectural layer categorization:
  - `Presentation`: UI components, pages, templates.
  - `API / Controller`: Endpoints, routers, request handlers.
  - `Business / Service`: Domain workflows and services.
  - `Data / Model`: Schemas, ORM models, migrations.
  - `Core / Infrastructure`: Configuration, middleware, utilities.
  - `Test`: Unit and integration test suites.

### Stage 4: Dependency Extraction & Resolution
- Resolves relative imports (`from ..models.user import User`, `import { x } from '../api'`) to exact target files in the repository.
- Distinguishes relationship types: `import`, `calls`, `inherits`, `contains`, `references`.
- Assigns certainty labels: `confirmed` (verified target), `inferred` (heuristic / global name match), `unresolved` (external vendor library).

### Stage 5: Graph Computation & Cycle Detection
- Directed graph constructed using NetworkX.
- Calculates in-degree (dependents), out-degree (dependencies), and degree centrality.
- Identifies circular dependencies using Tarjan's strongly connected components (SCC) algorithm.
- Computes forward and reverse reachability trees for change impact analysis.

### Stage 6: Lexical & Full-Text Search Indexing
- Builds multi-index search across symbol names, file paths, and full source code lines.
- Generates 3-line context excerpts for full-text matches.

### Stage 7: Reporting
- Consolidates repository metrics, layer breakdowns, entry points, and structural limitations into a structured exportable markdown document.
