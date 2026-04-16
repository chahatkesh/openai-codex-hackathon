# Product Spec — What We Are Building
### OpenAI Codex Hackathon, Bengaluru · April 16, 2026

> **One sentence:** Connect your Codex to our MCP once, fund a wallet, and your agent can call any API in the world — no keys, no sign-ups, no integration code. If the API isn't in our catalog yet, our agents integrate it live while you watch.

---

## 1. The Product in Plain English

We are building the API execution layer for the agentic coding era.

Right now, when a developer or non-technical builder uses Codex to build something real — a monitoring tool, an automation, an AI workflow — the moment they need an external API (send an SMS, scrape a website, deliver an email, query a database), they have to stop. Sign up for the API. Understand the auth. Write the integration code. Store the credentials. This breaks the flow entirely and is often a blocker for non-technical builders.

Our product removes this wall. The user connects our single MCP server to Codex once. They fund a wallet once. From that point forward, their Codex agent can call any API in our catalog — Twilio, Nylas, Apify, Stripe, and hundreds more — without touching a credential, without writing a line of integration code, and without leaving Codex. Every call is billed in real time from their wallet.

When an API isn't in the catalog yet, our integration pipeline — a set of autonomous agents — discovers the API docs, generates the integration code, tests it against live endpoints, self-corrects errors, and adds the new tool to the catalog. The catalog grows itself.

---

## 2. Core Components

### 2.1 MCP Server

The MCP server is the primary interface between the user's Codex session and our platform. It is a single hosted endpoint that Codex connects to via the Model Context Protocol.

**What it does:**

- Responds to `tools/list` requests from Codex with the current catalog of available tools — every API integration we have live at that moment
- Responds to `tools/call` requests by executing the requested tool using our platform's stored credentials for that API provider
- Validates every incoming request against the user's session and wallet before executing
- Returns results to Codex in the standard MCP response format
- On a gap (Codex requests a tool that doesn't exist in the catalog), triggers the integration pipeline and notifies Codex to retry after integration completes
- Logs every call with timestamp, tool name, user, cost, and result status

**What it is not:**

- It does not generate code
- It does not store user credentials — it stores platform credentials only
- It does not decide which tools to call — Codex decides that

---

### 2.2 Living Catalog (the SKILL.md store)

The living catalog is the central database of tool definitions. It is the memory of the system. Every tool that Codex can call is defined here. Every integration the pipeline builds gets written here.

**What it contains per tool:**

- Tool name (e.g. `send_email`, `scrape_url`, `send_sms`)
- Description — plain English description of what the tool does and when to use it. This is what Codex reads to decide when to call it.
- Input schema — the fields the tool accepts, their types, and which are required
- Output schema — what the tool returns
- Provider — which external API backs this tool (e.g. Nylas, Apify, Twilio)
- Cost per call — how many credits this tool costs to call
- Status — `live`, `pending_credentials`, `deprecated`
- Integration method — how the platform calls the external API (REST, GraphQL, SDK)
- Date added and who or what added it (manual seed or pipeline-generated)
- Version — tools can be updated without breaking callers

**Catalog states:**

- `live` — tool is callable right now
- `pending_credentials` — integration code has been generated and tested but the platform has not yet registered with the provider. Shown on marketplace as "coming soon."
- `deprecated` — old version of a tool, kept for backwards compatibility

---

### 2.3 Backend API

The backend API is the internal service layer that connects the MCP server, the marketplace website, the integration pipeline, and the database. It is not user-facing directly.

**What it exposes:**

- `GET /catalog` — full list of tools in the catalog with status, description, and cost
- `GET /catalog/recent` — tools added in the last 24 hours (used by the live feed on the website)
- `POST /integrate` — accepts a docs URL, triggers the integration pipeline, returns a job ID
- `GET /integrate/:job_id` — returns the status of an integration job (queued, running, complete, failed)
- `GET /wallet/balance` — returns the current credit balance for a user
- `POST /wallet/topup` — adds credits to a user's wallet
- `GET /usage` — returns call history, cost breakdown, and per-tool usage for a user
- `POST /users` — creates a new user account

---

### 2.4 Agentic Payments and Wallet System

The wallet is the billing infrastructure that makes "no keys, no setup" financially viable. Instead of per-user API key management, users pre-fund a credit wallet. Every tool call debits from the wallet in real time.

**What the wallet does:**

- Holds a credit balance per user, denominated in platform credits (credits map to USD at a fixed rate, e.g. 1000 credits = $1)
- Deducts the cost of each tool call atomically at the moment of execution — if the call fails, credits are refunded
- Blocks tool calls if the wallet balance is insufficient and returns a clear error to Codex
- Records every transaction with tool name, timestamp, cost, and call outcome
- Supports top-up via Stripe or manual credit grant (for hackathon: manual grant only)

**Pricing model (per tool call):**

- Scraping and data retrieval — higher cost per call (compute-heavy)
- Messaging (SMS, email) — medium cost per call (per-unit pricing from providers passed through)
- Search and lightweight lookups — lowest cost per call
- Integration pipeline execution — flat fee per integration (billed once when a new tool is created)

**Agent spending controls:**

- Per-session spend limit — a maximum number of credits a single Codex session can spend. Codex is told the limit upfront via a system prompt or tool metadata. Prevents runaway agent loops from draining the wallet.
- Low balance alert — when balance drops below a configurable threshold, the MCP server includes a warning in the next tool call response so Codex can surface it to the user
- Spend summary — after every session, the platform can return a breakdown of what was called and what it cost

**What agentic payments enables:**

- A Codex agent running a long autonomous task (scraping 50 pages, sending 100 emails) can execute end-to-end without any human approval per step — the wallet is the authorization
- The spend limit is the only guardrail the user sets. Within that limit, the agent acts completely autonomously.
- This is meaningfully different from OAuth flows or per-call approvals — it is designed for continuous, non-interactive agent execution

---

### 2.5 Integration Pipeline

The integration pipeline is the autonomous system that adds new tools to the catalog. It is a sequence of four agents, each with a specific job, running in order. It is triggered either by the crawler or by a user dropping a docs URL.

**The four agents:**

**Agent 1 — Discovery**
Given a starting point (a docs URL, an API name, or a topic), this agent figures out what API to integrate and where the full documentation lives. It extracts: the API's base URL, authentication method (API key, OAuth, Bearer token, no auth), available endpoints, rate limits, and any sandbox or test environment details.

**Agent 2 — Reader**
Given the docs URL from Agent 1, this agent reads and parses the documentation fully and autonomously. It extracts: endpoint paths, HTTP methods, required and optional parameters, request body schemas, response schemas, error codes and their meanings, and authentication header format. It produces a structured JSON representation of the API's surface.

**Agent 3 — Code Generator**
Given the structured API representation from Agent 2, this agent writes a Python wrapper function that: accepts the tool's input schema parameters, constructs the correct API request, handles authentication using the platform's stored credentials, parses the response into a clean output, and handles the most common error cases with clear messages. The function must match the tool definition format expected by the catalog.

**Agent 4 — Tester and Fixer**
Given the wrapper function from Agent 3, this agent tests it against real API endpoints. It: constructs a valid test call using sandbox credentials or free-tier endpoints, executes the call, inspects the response, and if the call fails, reads the error, identifies the problem in the code, patches the function, and retries. It does this up to three times. If all three attempts fail, it marks the integration as failed and logs the errors for review. If it succeeds, it writes the validated tool definition to the catalog with status `live` (or `pending_credentials` if credentials are not yet stored).

**What triggers the pipeline:**

- A docs URL submitted via the marketplace website's request form
- The crawler identifying a new API worth integrating
- A Codex session requesting a tool that doesn't exist in the catalog (real-time trigger)

**What the pipeline does not do:**

- It does not obtain API credentials. It generates the code and tests it. Credentials are a separate step.
- It does not guarantee the integration works for all edge cases — it validates the happy path
- It does not handle APIs that require OAuth user-level authentication (only platform-level API key auth is in scope)

---

### 2.6 Crawler

The crawler is a background agent that runs continuously and discovers new APIs worth integrating into the catalog.

**What it does:**

- Periodically scans sources: Product Hunt (new API tools), GitHub trending repositories with "API" in the description, APIs.guru (a public directory of OpenAPI specs), Hacker News "Show HN" posts mentioning APIs, RapidAPI marketplace new listings
- For each candidate, evaluates whether it is worth integrating based on: whether it has public documentation, whether it uses standard API key auth, whether it is likely to be useful to Codex agents (i.e. takes actions in the world — sends something, retrieves something, creates something)
- Deduplicates against the existing catalog — does not re-integrate APIs already present
- Triggers the integration pipeline for approved candidates
- Logs every candidate it evaluated and the decision (integrate / skip / manual review)

**What the crawler is not:**

- It is not real-time — it runs on a schedule (every few hours)
- It is not autonomous on credentials — it can generate integrations but cannot register with APIs
- For the hackathon, the crawler is the lowest-priority component. The integration pipeline triggered manually is sufficient for the demo.

---

### 2.7 Marketplace Website

The marketplace website is the user-facing frontend of the platform. It is where users discover available tools, fund their wallet, connect their Codex, and watch the catalog grow in real time.

**Pages and features:**

**Catalog page**
- Lists every tool in the catalog
- Each listing shows: tool name, what it does in plain English, which provider backs it, cost per call, and status badge (live / coming soon)
- Search and filter by category (communication, data retrieval, payments, etc.)
- Sort by: newest, most called, lowest cost

**Live integration feed**
- A real-time panel showing integration activity
- Displays: name of API being integrated, current pipeline stage (discovering / reading / generating / testing), and time elapsed
- When an integration completes, the new tool appears in the feed with a "live" badge
- Shows a running counter: "X tools in catalog · Y added today"
- This is designed to be shown on a projector during the demo

**Request an integration**
- A form where a user pastes a docs URL or API name
- Submits to the integration pipeline
- Shows live progress of the integration job
- Notifies when the new tool is available

**Connect Codex**
- Step-by-step instructions for adding the MCP server URL to Codex settings
- The user's unique MCP endpoint URL (authenticated per user)
- Copy button

**Wallet**
- Current credit balance
- Top-up form
- Full transaction history: every tool call, timestamp, cost, and result
- Per-tool usage breakdown (how many times each tool was called this week, total spend)
- Session spend summary

**Account**
- Email, name
- Agent spending limit setting (max credits per Codex session)
- Low-balance alert threshold

---

## 3. Data Models

### User
- ID, email, name, created at
- MCP auth token (unique per user, used to authenticate Codex connection)
- Wallet balance (credits)
- Spending limit per session
- Low-balance alert threshold

### Tool Definition
- ID, name, description, provider
- Input schema (JSON Schema)
- Output schema (JSON Schema)
- Implementation code (Python function, stored server-side)
- Cost per call (credits)
- Status (live / pending_credentials / deprecated)
- Source (manual / pipeline / seed)
- Created at, updated at
- Version number

### API Credential
- Provider name (e.g. "nylas", "twilio")
- Credential type (api_key, bearer_token)
- Encrypted credential value
- Added at, last used at
- This is a platform-level record, not per-user

### Tool Call Log
- ID, user ID, tool name
- Input arguments (sanitised — no PII)
- Result status (success / error)
- Error message if failed
- Credits deducted
- Execution duration (ms)
- Timestamp

### Wallet Transaction
- ID, user ID
- Type (debit / credit)
- Amount (credits)
- Reference (tool call log ID for debits, top-up ID for credits)
- Balance after transaction
- Timestamp

### Integration Job
- ID, docs URL
- Status (queued / discovering / reading / generating / testing / complete / failed)
- Current agent stage
- Attempts made by Test+Fix agent
- Error log
- Resulting tool ID (if complete)
- Triggered by (crawler / user / codex session)
- Created at, completed at

---

## 4. User Flows

### Flow 1 — First-time setup (one time only)
1. User creates an account on the marketplace website
2. User tops up their wallet with credits
3. User copies their unique MCP server URL from the "Connect Codex" page
4. User adds that URL to their Codex settings
5. Done. Codex now has access to the full catalog.

### Flow 2 — Using an existing tool (happy path)
1. User types a prompt in Codex: "Monitor Product Hunt for AI tools and email me a digest every morning"
2. Codex calls `tools/list` on the MCP server
3. MCP server returns: `scrape_url`, `send_email`, `schedule_task` and other available tools
4. Codex executes the task: calls `scrape_url` for Product Hunt, processes the data, calls `send_email` with the digest
5. Each call debits the user's wallet
6. The email arrives in the user's inbox

### Flow 3 — Gap detected, live integration (the demo moment)
1. Codex needs a tool that isn't in the catalog (e.g. Resend email API)
2. MCP server returns a tool-not-found response and triggers the integration pipeline with the Resend docs URL
3. On the marketplace website's live feed, the integration job appears: "Integrating Resend API"
4. The four agents run in sequence — visible on the live feed
5. The Test+Fix agent encounters an auth error, corrects the code, retries — this is visible
6. Integration completes. New tool `send_email_resend` appears in the catalog as live.
7. Codex retries the original tool call. It succeeds.
8. The email is delivered.

### Flow 4 — User requests an integration manually
1. User sees on the marketplace that an API they want isn't in the catalog
2. User pastes the docs URL into the "Request an integration" form
3. Integration pipeline runs (same as Flow 3 from step 3 onward)
4. User gets notified when the tool is live

### Flow 5 — Wallet runs low mid-session
1. Codex agent is running a long autonomous task
2. Wallet drops below the user's alert threshold
3. MCP server includes a low-balance warning in the next tool call response
4. Codex surfaces the warning to the user
5. If balance hits zero, the MCP server blocks further calls and returns a clear "insufficient balance" error

---

## 5. What Is In Scope vs Out of Scope

### In Scope (build this)
- MCP server with tools/list and tools/call
- Living catalog database with tool definitions
- Platform credential store for pre-registered API providers (Twilio, Nylas, Apify, Product Hunt)
- Wallet system with credit balance, per-call deduction, and spend limits
- Integration pipeline (all four agents)
- Marketplace website with catalog, live feed, wallet, and connect instructions
- Backend API serving both MCP server and website
- Pre-seeded catalog with 5-8 live integrations
- The demo scenario: Product Hunt digest (scrape → summarise → email)
- The live integration demo: drop a docs URL, watch integration run, call the new tool

### Out of Scope for Hackathon (do not build)
- Crawler (background API discovery) — manually trigger the pipeline instead
- OAuth-based user-level API authentication — platform-level keys only
- Stripe payment integration — mock wallet top-up
- User authentication and login — hardcode a single demo user
- Rate limiting and abuse prevention
- Production error handling and retries at the infrastructure level
- Mobile-responsive design
- Multi-tenancy at the credential level (all users share platform credentials)
- API versioning and backwards compatibility
- Admin dashboard
- Team accounts and collaboration

---

## 6. The Demo Scenario

The demo is the only thing that matters on the day. Every build decision should be evaluated against whether it makes the demo work better.

**The two-act demo:**

**Act 1 — The happy path (2 minutes)**
Open Codex. Type: "Monitor Product Hunt every day for new AI developer tools, summarise the top 3, and email them to rishi@example.com every morning."

Codex calls tools from the catalog. The audience watches tool calls execute. At the end, an email lands in the inbox live. The live feed on the projector shows the call activity.

**Act 2 — The live integration (90 seconds)**
Say: "Now watch what happens when Codex needs an API we've never integrated before."

The pipeline triggers for a new API (pre-chosen, docs URL ready). The live feed on the projector shows the four agents working: discovering, reading, generating code, testing, hitting an error, fixing, retrying, succeeding. The new tool appears in the catalog. Codex calls it. It works.

**What must be true for Act 2 to work:**
- The chosen new API has a sandbox or free tier that accepts calls without account creation
- The Test+Fix agent's self-correction is fast enough (under 90 seconds total)
- The live feed updates in real time and is visible on the projector
- The tool call after integration succeeds on the first retry

**The chosen new API for the live integration demo:**
Pick this before April 16. Criteria: clean REST docs, API key auth (no OAuth), free tier or sandbox, simple endpoint (one call does something visible). Resend (email API) or Loops.so are good candidates. Test the full pipeline with this API at least twice before the event.

---

## 7. The One-Paragraph Pitch

"Every time someone builds with Codex or Lovable and needs a real API — Twilio, Nylas, Apify, anything — they have to stop. Sign up. Get keys. Write the integration. That kills the flow entirely.

We remove that wall. You connect our MCP to Codex once. You fund a wallet once. From then on, your agent calls any API in our catalog — no keys, no setup, no integration code. Every call is billed in real time from your wallet.

And when the API isn't in our catalog yet? Watch."

[run Act 2]