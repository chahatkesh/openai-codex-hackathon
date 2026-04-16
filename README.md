<img width="3000" height="1000" alt="Git Repo Cover" src="https://github.com/user-attachments/assets/8ddae07c-14ee-4664-9711-5e06effcc5ef" />


# FuseKit 🔥

> **Describe what you want built. FuseKit figures out every API it needs — and integrates the ones it doesn't have yet, live, before your eyes.**

[![Built for OpenAI Codex Hackathon](https://img.shields.io/badge/OpenAI%20Codex-Hackathon%202026-412991)](https://openai.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://typescriptlang.org)
[![Turborepo](https://img.shields.io/badge/Turborepo-monorepo-EF4444)](https://turbo.build)

---

## What is FuseKit?

FuseKit is a **self-growing agentic system** that takes a single natural language prompt and autonomously figures out, integrates, and executes every API it needs to complete the task — including APIs it has never seen before.

Most AI coding tools assume you already know which APIs you need. FuseKit doesn't. When it hits a capability gap, it doesn't stop and ask you. It spins up five integration agents that find the right API, read the docs, generate working code, test it against live endpoints, and write the validated integration into its **living catalog** — all before your request finishes running.

**Every request makes FuseKit smarter. The catalog grows itself.**

---

## The Demo

**User types:**
```
Monitor Product Hunt daily, find any AI dev tools launched this week,
scrape their landing pages, and email me a digest every morning.
```

**What happens next — live, on screen:**

| Step | What you see | What it means |
|------|-------------|---------------|
| Planner decomposes request | 3 capabilities identified | Scheduling, scraping, email |
| Catalog check | Scraping ✅ Email ✅ Product Hunt ❌ | Gap detected |
| Agent 1 activates | Searching for Product Hunt API | "It knows what it doesn't know" |
| Agent 2 activates | Reading PH API v2 docs | No human input |
| Agent 3 activates | Generating integration code | Live code appearing |
| Agent 4 activates | Testing against live endpoint → error → self-corrects | "It just taught itself" |
| Agent 5 activates | Writing to living catalog | Catalog visibly grows |
| Pipeline resumes | All 3 integrations called via MCP | Everything wired |
| **Final moment** | **Digest email lands in inbox** | **Real. Undeniable.** |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Prompt (NL)                      │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Planner Agent                         │
│         Decomposes request → required capabilities       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Living Catalog Check                     │
│              Reads SKILL.md — gap detected?              │
└────────────┬──────────────────────────────┬─────────────┘
             │ YES — use existing            │ NO — trigger integration
             ▼                              ▼
┌────────────────────┐     ┌───────────────────────────────┐
│   Call via MCP     │     │      Integration Agents        │
│   immediately      │     │                               │
└────────────────────┘     │  Agent 1 → Find right API     │
                           │  Agent 2 → Read docs          │
                           │  Agent 3 → Generate code      │
                           │  Agent 4 → Test + self-correct│
                           │  Agent 5 → Write to SKILL.md  │
                           └──────────────┬────────────────┘
                                          │ catalog updated
                                          ▼
                           ┌─────────────────────────────┐
                           │     MCP Execution Layer      │
                           │  Single gateway — all skills │
                           └──────┬──────────┬────────────┘
                                  │          │
                    ┌─────────────┘          └──────────────┐
                    ▼                                        ▼
          ┌──────────────────┐                   ┌─────────────────────┐
          │  Scraper (Apify) │                   │  Email (Resend)     │
          │  PH Monitor      │                   │  Twilio SMS         │
          └──────────────────┘                   └─────────────────────┘
                    │                                        │
                    └──────────────┬─────────────────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │  Real output — digest email   │
                    │  lands in inbox, live         │
                    └──────────────────────────────┘
```

---

## How SKILL.md Works

SKILL.md is FuseKit's **living catalog** — a plain text file that acts as shared memory across all agents. Think of it as a recipe book that writes itself.

Every time FuseKit integrates a new API, Agent 5 appends a validated entry:

```markdown
## Product Hunt API
- **Purpose**: Fetch newly launched products by category and date
- **Auth**: Bearer token — Authorization: Bearer <token>
- **Endpoint**: POST https://api.producthunt.com/v2/api/graphql
- **Working snippet**:
  ```typescript
  const res = await fetch('https://api.producthunt.com/v2/api/graphql', {
    method: 'POST',
    headers: { Authorization: `Bearer ${process.env.PH_TOKEN}` },
    body: JSON.stringify({ query: `{ posts(order: NEWEST) { edges { node { name tagline url } } } }` })
  })
  ```
- **Rate limit**: 500 requests/day
- **Notes**: Pagination via cursor. Filter by topic slug for categories.
- **Added**: 2026-04-11 | **Tested**: ✅ | **Agent**: auto-integrated
```

Next time any request needs Product Hunt data — it's there. No re-integration needed.

---

## Real World Examples

### Example 1 — Morning digest (the demo)
```
"Monitor Product Hunt daily, find AI dev tools launched this week,
scrape their landing pages, and email me a digest every morning."
```
**APIs integrated:** Product Hunt API v2, Apify web scraper, Resend email
**Output:** Daily email at 8am with titles, descriptions, and landing page summaries

---

### Example 2 — Competitor monitoring
```
"Watch my 3 competitors' pricing pages. If any price changes,
send me a Twilio SMS immediately."
```
**APIs integrated:** Apify scraper (existing), Twilio SMS (new — integrated live)
**Output:** Real-time SMS alert when pricing HTML changes

---

### Example 3 — GitHub activity digest
```
"Every Friday, find trending GitHub repos in Rust from this week,
summarize what each one does, and post a thread to my Slack."
```
**APIs integrated:** GitHub REST API (new), Slack webhooks (new), OpenAI summarization
**Output:** Weekly Slack thread posted automatically every Friday

---

### Example 4 — Lead enrichment
```
"Take this list of company names, find their LinkedIn pages,
scrape the employee count and industry, and email me a CSV."
```
**APIs integrated:** LinkedIn scraper via Apify, Resend email (existing)
**Output:** Enriched CSV delivered to inbox in under 2 minutes

---

### Example 5 — Support ticket routing
```
"Watch our Intercom inbox. If a message contains the word 'refund',
create a Notion task and ping the #billing Slack channel."
```
**APIs integrated:** Intercom webhooks (new), Notion API (new), Slack (existing)
**Output:** Zero-touch ticket routing between three platforms

---

## Tech Stack

### Frontend
| Tool | Purpose |
|------|---------|
| Next.js 15 | Web app + API routes |
| TypeScript | End to end type safety |
| Tailwind CSS | Styling |
| Server-Sent Events | Live agent status streaming to UI |

### Agent Runtime
| Tool | Purpose |
|------|---------|
| OpenAI Codex | Powers all 5 integration agents |
| LangChain / custom | Agent orchestration |
| Node.js | Agent execution runtime |

### Integrations (pre-loaded in catalog)
| Service | Purpose | Skill in catalog |
|---------|---------|-----------------|
| Apify | Web scraping | ✅ pre-loaded |
| Resend | Transactional email | ✅ pre-loaded |
| Twilio | SMS alerts | ✅ pre-loaded |
| Product Hunt API | Launch monitoring | ⚡ integrated live in demo |
| Slack Webhooks | Team notifications | ⚡ integrated on demand |
| GitHub REST API | Repo data | ⚡ integrated on demand |

### Infrastructure
| Tool | Purpose |
|------|---------|
| Turborepo | Monorepo management |
| MCP (Model Context Protocol) | Single gateway for all integrations |
| SKILL.md | Living catalog — zero database needed |

---

## Repo Structure

```
fusekit/
├── apps/
│   ├── web/                        # Next.js frontend
│   │   ├── app/
│   │   │   ├── page.tsx            # Prompt input UI
│   │   │   ├── demo/page.tsx       # Live agent panel
│   │   │   └── api/
│   │   │       ├── run/route.ts    # Triggers planner agent
│   │   │       └── catalog/route.ts # Streams SKILL.md updates
│   │   └── components/
│   │       ├── PromptInput.tsx     # User types request
│   │       ├── AgentPanel.tsx      # 5 agents working live
│   │       ├── CatalogViewer.tsx   # SKILL.md growing on screen
│   │       └── OutputPanel.tsx     # Final result display
│   │
│   └── agents/                     # Agent runtime
│       ├── planner.ts              # Decomposes prompt → capabilities
│       ├── gap-detector.ts         # Checks SKILL.md for missing skills
│       ├── executor.ts             # Calls MCP with resolved skills
│       └── integration/
│           ├── api-finder.ts       # Agent 1 — finds right API
│           ├── doc-reader.ts       # Agent 2 — reads docs autonomously
│           ├── code-generator.ts   # Agent 3 — generates integration code
│           ├── tester.ts           # Agent 4 — tests + self-corrects
│           └── skill-writer.ts     # Agent 5 — writes to SKILL.md
│
├── packages/
│   ├── catalog/                    # SKILL.md read/write
│   │   ├── reader.ts               # Parse SKILL.md → structured data
│   │   ├── writer.ts               # Append new skill entries
│   │   └── SKILL.md                # The living catalog
│   │
│   ├── mcp/                        # MCP gateway
│   │   ├── client.ts               # Single MCP client
│   │   └── tools/
│   │       ├── apify.ts            # Scraping (pre-loaded)
│   │       ├── resend.ts           # Email (pre-loaded)
│   │       ├── twilio.ts           # SMS (pre-loaded)
│   │       └── [dynamic].ts        # Generated at runtime by Agent 5
│   │
│   └── utils/
│       ├── cache.ts                # API response cache (demo safety)
│       ├── mutex.ts                # SKILL.md write lock
│       └── retry.ts                # Agent retry with backoff
│
├── SKILL.md                        # Root living catalog
├── turbo.json
├── package.json
└── tsconfig.json
```

---

## Getting Started

### Prerequisites
- Node.js 20+
- pnpm 8+
- OpenAI API key (Codex access)

### Installation

```bash
git clone https://github.com/yourteam/fusekit
cd fusekit
pnpm install
```

### Environment Variables

```bash
# .env.local
OPENAI_API_KEY=sk-...
APIFY_API_TOKEN=apify_...
RESEND_API_KEY=re_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...
PH_TOKEN=                    # Product Hunt — integrated live in demo
```

### Run locally

```bash
pnpm dev
```

Opens at `http://localhost:3000`

---

## Error Handling Strategy

FuseKit uses **demo-safe** error handling — not production-grade, but stage-proof.

| Error | Treatment | Why |
|-------|-----------|-----|
| API rate limit | Silent cache fallback | Never kills demo |
| Agent code gen fails | Visible retry on screen | This IS the wow moment |
| SKILL.md write conflict | Mutex lock + friendly message | Prevents silent corruption |
| Email delay | Pre-open inbox on phone | Venue wifi is unpredictable |
| LLM timeout | 3x retry with backoff | Codex can be slow under load |

The only error judges should *see* is Agent 4 self-correcting. Everything else recovers silently.

---

## The Two Wow Moments

### Moment 1 — "It knows what it doesn't know"
The planner detects a capability gap mid-task. The living catalog is missing Product Hunt. Five agents spin up on screen. This is the moment that separates FuseKit from every other agent demo.

### Moment 2 — "It just taught itself a new skill"
Agent 5 writes a new entry to the living catalog. On screen, judges watch the catalog gain a new block in real time. The system is now permanently smarter than it was 90 seconds ago.

### The closer — email arrives live
A real digest email lands in a real inbox during the presentation. Non-technical, visceral, undeniable proof that the whole pipeline worked end to end.

---

## Built at OpenAI Codex Hackathon — Bengaluru 2026

> "Describe what you want. If the API exists in our catalog, it's called instantly. If it doesn't — watch our agents integrate it live, right now, and call it before your demo ends."

---

## License

MIT
