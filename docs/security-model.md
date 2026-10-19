# DevMind AI: Security Architecture & Threat Model

## Core Security Tenets

1. **Zero Execution Policy**: DevMind AI NEVER executes, installs, runs hooks, or interprets code found in ingested repositories. Analysis is strictly static (AST parsing and lexical indexing).
2. **SSRF (Server-Side Request Forgery) Defense**:
   - Only HTTP and HTTPS git URLs are permitted.
   - Hostnames resolving to private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `0.0.0.0`, `localhost`, link-local addresses) are strictly blocked.
3. **Zip Slip & Archive Traversal Protection**:
   - Path resolution checks ensure every uncompressed file stays within the sandboxed repository target directory.
   - Decompression bomb guard: enforces a maximum 200MB uncompressed limit and 10,000 maximum file count.
4. **Prompt Injection & Untrusted Code Guardrails**:
   - Repository source files, comments, and README contents are treated as untrusted data.
   - Code sent to AI context is wrapped in strict `<untrusted_code>` XML isolation blocks with instructions prohibiting instruction override.
5. **False-Positive Management**:
   - Static analysis findings from Ruff and Bandit can be marked as false positives with an audit reason, stored persistently in the database.
