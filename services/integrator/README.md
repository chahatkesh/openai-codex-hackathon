# Integrator Service

This service will host the integration pipeline:

1. discovery
2. reader
3. codegen
4. test/fix
5. publish

Recommended runtime: Python 3.11+ with FastAPI.

Publishing modules:

- `app/publishers/db_writer.py` writes validated generated tools to the platform DB for the local demo path.
- `app/publishers/github_pr/` publishes generated marketplace files through a safe GitHub draft-PR workflow. See `../../docs/github-pr-publishing.md`.
