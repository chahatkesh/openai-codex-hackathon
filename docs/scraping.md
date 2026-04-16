# Scraping And Integration Flow

This document explains how FuseKit now handles scraping, docs reading, integration, manifest storage, and later reuse.

It is written for the current implementation in this repo, not the older aspirational README language.

## Why This Exists

FuseKit should not treat API docs like a plain text dump.

When Codex asks for a capability that does not exist yet, the platform should:

1. trigger integration
2. read the provider docs properly
3. generate the tool
4. publish the tool runtime
5. store a reusable manifest JSON artifact
6. let later requests reuse that artifact

That is the purpose of the scraping and manifest flow.

## High-Level Flow

The current flow is:

1. Codex asks FuseKit MCP for a capability.
2. If the tool already exists, FuseKit can return the existing manifest/pointer.
3. If the tool does not exist, FuseKit queues an integration job.
4. The integrator fetches and structures the docs.
5. Discovery and reader agents extract API information.
6. Codegen generates the runtime tool.
7. Test/fix validates the generated code.
8. Publish stores:
   - the tool row in DB
   - the generated runtime Python file
   - the manifest JSON file
9. Later, FuseKit can return the manifest again for reuse.

## What "Scraping" Means In FuseKit

In this project, scraping is no longer just "fetch a page and strip HTML."

The scraping/docs reader now tries to understand the source type and handle it properly.

It supports:

- HTML docs pages
- OpenAPI or Swagger JSON/YAML
- PDFs
- optionally JS-rendered pages through Playwright when available

The important idea is:

- raw fetch is for retrieval
- structured extraction is for machines
- docs bundle is for Codex/codegen
- manifest is the reusable published artifact

## Current Components

### Platform MCP scraper

File:

- [services/platform/app/tools/scrape_url.py](/home/harsh/projects/openai-codex-hackathon/services/platform/app/tools/scrape_url.py)

What it does now:

- fetches a URL
- detects content type
- extracts structured data from HTML
- parses OpenAPI docs when possible
- parses PDFs when `pypdf` is installed
- returns JSON text instead of one plain text blob

Example return shape:

```json
{
  "url": "https://docs.example.com/auth",
  "content_type": "text/html",
  "title": "Authentication",
  "summary": "Use Bearer tokens in the Authorization header.",
  "text": "Clean extracted page text...",
  "headings": ["Authentication", "Errors"],
  "code_blocks": ["curl -H \"Authorization: Bearer token\" ..."],
  "links": ["https://docs.example.com/reference"],
  "endpoint_hints": ["POST /messages"],
  "auth_hints": ["Use Bearer tokens in the Authorization header."],
  "metadata": {
    "status_code": 200,
    "final_url": "https://docs.example.com/auth"
  }
}
```

### Integrator docs fetcher

File:

- [services/integrator/app/docs_fetcher.py](/home/harsh/projects/openai-codex-hackathon/services/integrator/app/docs_fetcher.py)

What it does now:

- fetches docs with limits from config
- builds structured `DocumentPage` objects
- chooses useful same-site pages like auth, reference, errors, guides
- formats multiple pages into one normalized docs bundle
- optionally renders JS-heavy docs pages with Playwright

This is the input used by:

- [services/integrator/app/agents/discovery.py](/home/harsh/projects/openai-codex-hackathon/services/integrator/app/agents/discovery.py)
- [services/integrator/app/agents/reader.py](/home/harsh/projects/openai-codex-hackathon/services/integrator/app/agents/reader.py)

## Request Integration Flow

The request flow starts in:

- [services/platform/app/tools/request_integration.py](/home/harsh/projects/openai-codex-hackathon/services/platform/app/tools/request_integration.py)

This tool now has two behaviors.

### Case 1: Tool already exists

If `requested_tool_name` already exists in the live catalog:

1. FuseKit loads the tool from DB.
2. FuseKit loads the stored manifest if present.
3. If no manifest file exists, FuseKit synthesizes a fallback manifest.
4. FuseKit returns JSON with:
   - `status: "already_available"`
   - manifest contents
   - manifest pointer

This is handled through:

- [services/platform/app/services/manifest_service.py](/home/harsh/projects/openai-codex-hackathon/services/platform/app/services/manifest_service.py)

### Case 2: Tool does not exist

If the tool is missing:

1. FuseKit creates an `integration_jobs` row.
2. FuseKit stores the docs URL or generates a discovery URL.
3. FuseKit forwards the job to the integrator.
4. FuseKit returns JSON with:
   - `status: "integration_requested"`
   - `job_id`
   - `docs_url`
   - `requested_tool_name`

## Pipeline Flow

The integration pipeline is orchestrated in:

- [services/integrator/app/pipeline.py](/home/harsh/projects/openai-codex-hackathon/services/integrator/app/pipeline.py)

Stages:

1. `discovery`
2. `reader`
3. `codegen`
4. `test_fix`
5. `publish`

### 1. Discovery

Discovery reads a compact docs bundle and tries to infer:

- provider name
- base URL
- auth type
- key endpoints
- rate limit hints

### 2. Reader

Reader consumes a larger documentation bundle and produces a structured API spec:

- endpoints
- auth structure
- error structure
- provider/base URL

### 3. Codegen

Codegen turns the API spec into:

- tool definition metadata
- Python runtime code

### 4. Test/Fix

Test/fix imports the generated Python code and checks that:

- `execute(**kwargs)` exists
- it returns a string

If it fails, the LLM is asked to repair it.

### 5. Publish

Publish is implemented in:

- [services/integrator/app/publishers/db_writer.py](/home/harsh/projects/openai-codex-hackathon/services/integrator/app/publishers/db_writer.py)

Publish now stores three artifacts:

1. Tool row in DB
2. Runtime Python file
3. Manifest JSON file

Runtime files are stored under:

- `/tmp/fusekit_dynamic_tools/<tool_name>.py`

Manifest files are stored under:

- `/tmp/fusekit_dynamic_tools/manifests/<tool_name>.json`

## What The Manifest Contains

The manifest is the reusable integration artifact.

Today it includes:

- `tool_name`
- `provider`
- `status`
- `category`
- `source`
- `version`
- `description`
- `docs_url`
- integration job metadata
- discovery output
- API spec output
- tool definition fields
- runtime artifact paths
- test result summary

This gives the platform a stable artifact that later requests can reuse without re-running the whole integration logic.

## Example Flow For This Platform

### Example request

Codex needs:

`send_slack_message`

but that tool is not currently in the FuseKit catalog.

### Step-by-step

1. Codex calls FuseKit MCP and asks for a Slack sending capability.

2. FuseKit sees the tool is not live.

3. Codex or the platform calls `request_integration` with:

```json
{
  "capability_description": "Send Slack messages to a channel",
  "requested_tool_name": "send_slack_message"
}
```

4. FuseKit creates an integration job and returns:

```json
{
  "status": "integration_requested",
  "message": "Integration requested for 'send_slack_message'. FuseKit will attempt discovery, code generation, testing, and publish.",
  "job_id": "...",
  "docs_url": "https://www.google.com/search?q=send%20slack%20message+API+documentation",
  "requested_tool_name": "send_slack_message"
}
```

5. The integrator fetches docs pages related to Slack.

6. The docs fetcher builds a normalized bundle with information like:

- auth hints
- important headings
- endpoint hints
- code examples
- cleaned content

7. Discovery and reader extract the structured API information.

8. Codegen creates:

- generated tool metadata
- generated Python `execute()` implementation

9. Test/fix validates the tool.

10. Publish writes:

- a DB row for `send_slack_message`
- `/tmp/fusekit_dynamic_tools/send_slack_message.py`
- `/tmp/fusekit_dynamic_tools/manifests/send_slack_message.json`

11. On a later request, if Codex asks again for `send_slack_message`, `request_integration` can immediately return:

```json
{
  "status": "already_available",
  "message": "Tool 'send_slack_message' is already live.",
  "manifest": {
    "tool_name": "send_slack_message",
    "provider": "Slack",
    "...": "..."
  },
  "pointer": {
    "tool_name": "send_slack_message",
    "manifest_path": "/tmp/fusekit_dynamic_tools/manifests/send_slack_message.json"
  }
}
```

That means FuseKit no longer has to rediscover the integration from scratch.

## Why This Architecture Is Good

This architecture is useful because it separates concerns cleanly:

- scraper/docs fetcher gets the source material
- discovery/reader understand the docs
- codegen builds the runtime
- publish stores reusable artifacts
- platform runtime executes tools later
- manifest provides reuse and traceability

It also keeps the generated app or runtime pointed at FuseKit endpoints and FuseKit-managed artifacts, rather than forcing direct provider integration logic everywhere else.

## Current Limits

This is the current state, not the final ideal state.

Still true today:

- manifest storage is local filesystem based, not S3/object storage
- seeded tools use synthesized fallback manifests unless a real manifest file exists
- MCP does not yet expose a dedicated `get_tool_manifest` tool
- Playwright rendering depends on package and browser install being available locally

## Recommended Next Step

The clean next improvement would be:

- add a dedicated MCP tool like `get_tool_manifest`

That would make manifest retrieval explicit instead of piggybacking on `request_integration`.
