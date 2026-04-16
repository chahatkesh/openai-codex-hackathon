"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Code2,
  Copy,
  FileCode2,
  Network,
  ShieldCheck,
  WalletCards,
  Zap,
} from "lucide-react";
import { apiBaseUrl } from "@/lib/api";

const endpoint = `${apiBaseUrl}/mcp/http`;
const demoToken = "demo-token-fusekit-2026";

const credentials = [
  { key: "transport", label: "Transport", value: "Streamable HTTP", copyable: false, hint: "MCP protocol over HTTP" },
  { key: "url", label: "Server URL", value: endpoint, copyable: true, hint: "Paste this into your client" },
  { key: "token", label: "Bearer Token", value: demoToken, copyable: true, hint: "Authorization header value" },
];

const clients = [
  {
    key: "vscode",
    label: "VS Code",
    icon: FileCode2,
    tone: "bg-[color:var(--read)]",
    eyebrow: "Workspace setup",
    summary: "Connect inside the project so agent tools travel with the workspace.",
    steps: [
      "Open the Command Palette and run \u201cMCP: Add Server\u201d.",
      "Choose HTTP transport and name the server fusekit.",
      "Paste the Server URL and bearer token from above.",
      "Save, then refresh tools from the chat or agent panel.",
    ],
    codeLabel: ".vscode/mcp.json",
    code: `{
  "servers": {
    "fusekit": {
      "type": "http",
      "url": "${endpoint}",
      "headers": {
        "Authorization": "Bearer ${demoToken}"
      }
    }
  }
}`,
  },
  {
    key: "codex",
    label: "Codex App",
    icon: Network,
    tone: "bg-[color:var(--thinking)]",
    eyebrow: "Desktop setup",
    summary: "Add FuseKit once and every Codex session can discover the live catalog.",
    steps: [
      "Open Codex settings and create a new MCP server.",
      "Set transport to Streamable HTTP, name it fusekit.",
      "Use bearer token auth with the demo token above.",
      "Save, reconnect, then verify tools/list.",
    ],
    codeLabel: "Connection fields",
    code: `Name:          fusekit
Transport:     Streamable HTTP
URL:           ${endpoint}
Authorization: Bearer ${demoToken}`,
  },
  {
    key: "cli",
    label: "CLI",
    icon: Code2,
    tone: "bg-[color:var(--grep)]",
    eyebrow: "Terminal setup",
    summary: "Fastest path for local demos, scripts, and repeatable setup.",
    steps: [
      "Export the demo token in the shell that launches Codex.",
      "Register FuseKit as a remote MCP server.",
      "Run the list command to confirm it is installed.",
      "Start Codex and verify tools/list returns live tools.",
    ],
    codeLabel: "Shell",
    code: `export FUSEKIT_MCP_TOKEN="${demoToken}"

codex mcp add fusekit \\
  --url "${endpoint}" \\
  --bearer-token-env-var FUSEKIT_MCP_TOKEN

codex mcp list`,
  },
];

const verificationSteps = [
  {
    label: "Discover",
    command: "tools/list",
    detail: "scrape_url, send_email, send_sms visible",
    tone: "bg-[color:var(--read)]",
  },
  {
    label: "Execute",
    command: "tools/call",
    detail: "Run scrape_url then send_email or send_sms",
    tone: "bg-[color:var(--grep)]",
  },
  {
    label: "Spend",
    command: "wallet.check",
    detail: "Wallet middleware runs before routing",
    tone: "bg-[color:var(--thinking)]",
  },
  {
    label: "Grow",
    command: "TOOL_NOT_FOUND",
    detail: "Missing tool triggers the integration pipeline",
    tone: "bg-[color:var(--edit)]",
  },
];

export default function ConnectPage() {
  const [activeKey, setActiveKey] = useState("vscode");
  const [copied, setCopied] = useState<string | null>(null);

  function copy(key: string, value: string) {
    navigator.clipboard.writeText(value).catch(() => {});
    setCopied(key);
    setTimeout(() => setCopied(null), 1800);
  }

  const client = clients.find((c) => c.key === activeKey)!;
  const ClientIcon = client.icon;

  return (
    <section className="space-y-8 pb-16">

      {/* ── Header ── */}
      <header className="surface-card-light p-6 sm:p-8">
        <p className="eyebrow">MCP setup</p>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="section-title text-[color:var(--text)]">Connect to Codex</h1>
            <p className="body-serif mt-2 max-w-2xl">
              One Streamable HTTP server works across VS Code, the Codex app, and the CLI.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="flex items-center gap-1.5 rounded-full border table-rule bg-[color:var(--surface)] px-3 py-1.5 text-xs text-[color:var(--success)]">
              <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--success)]" aria-hidden="true" />
              Live endpoint
            </span>
            <Link href="/wallet" className="button-warm shrink-0">
              <WalletCards size={14} />
              Check wallet
            </Link>
          </div>
        </div>
      </header>

      {/* ── Credentials ── */}
      <div aria-label="Connection credentials">
        <p className="eyebrow mb-3">Credentials</p>
        <div className="overflow-hidden rounded-[8px] border table-rule divide-y divide-[color:var(--border)]">
          {credentials.map((cred) => (
            <div
              key={cred.key}
              className="flex items-center justify-between gap-4 bg-[color:var(--surface-light)] px-4 py-3.5"
            >
              <div className="flex min-w-0 flex-1 items-baseline gap-4">
                <p className="eyebrow w-24 shrink-0">{cred.label}</p>
                <p className="mono-text min-w-0 truncate text-[0.8rem] text-[color:var(--text)]">
                  {cred.key === "token" ? "\u2022".repeat(28) : cred.value}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <p className="hidden text-[0.68rem] text-[color:var(--text-soft)] sm:block">{cred.hint}</p>
                {cred.copyable ? (
                  <button
                    onClick={() => copy(cred.key, cred.value)}
                    className={`flex items-center gap-1.5 rounded px-2.5 py-1.5 text-[0.7rem] transition-colors ${
                      copied === cred.key
                        ? "bg-[color:var(--surface-strong)] text-[color:var(--success)]"
                        : "text-[color:var(--text-soft)] hover:bg-[color:var(--surface-strong)] hover:text-[color:var(--text)]"
                    }`}
                    aria-label={`Copy ${cred.label}`}
                  >
                    {copied === cred.key ? (
                      <><Check size={11} /> Copied</>
                    ) : (
                      <><Copy size={11} /> Copy</>
                    )}
                  </button>
                ) : (
                  <div className="w-[4.5rem]" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Client setup ── */}
      <section aria-label="Client setup">
        <p className="eyebrow mb-3">Client setup</p>

        {/* Tab strip */}
        <div
          className="surface-card-light overflow-hidden rounded-[8px] border table-rule"
        >
          {/* Tabs */}
          <div
            className="flex border-b table-rule"
            role="tablist"
            aria-label="Choose a client"
          >
            {clients.map((c) => {
              const Icon = c.icon;
              const active = c.key === activeKey;
              return (
                <button
                  key={c.key}
                  role="tab"
                  aria-selected={active}
                  onClick={() => setActiveKey(c.key)}
                  className={`relative flex items-center gap-2 px-5 pb-3 pt-3 text-sm transition-colors ${
                    active
                      ? "text-[color:var(--text)]"
                      : "text-[color:var(--text-soft)] hover:text-[color:var(--text-muted)]"
                  }`}
                >
                  <span
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded ${active ? c.tone : "bg-[color:var(--surface-strong)]"}`}
                    aria-hidden="true"
                  >
                    <Icon size={11} />
                  </span>
                  {c.label}
                  {active && (
                    <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-[color:var(--text)]" aria-hidden="true" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab panel */}
          <div role="tabpanel" className="grid gap-0 lg:grid-cols-[1fr_1.3fr] lg:divide-x lg:divide-[color:var(--border)]">

            {/* Steps */}
            <div className="p-5 sm:p-6">
              <p className="text-xs text-[color:var(--text-soft)]">{client.summary}</p>
              <ol className="mt-5 space-y-0" aria-label={`${client.label} setup steps`}>
                {client.steps.map((step, i) => {
                  const isLast = i === client.steps.length - 1;
                  return (
                    <li key={step} className="flex gap-3.5">
                      {/* Number + connector */}
                      <div className="flex flex-col items-center">
                        <span className="mono-text flex h-5 w-5 shrink-0 items-center justify-center rounded-full border table-rule bg-[color:var(--surface-strong)] text-[0.6rem] text-[color:var(--text-muted)]">
                          {i + 1}
                        </span>
                        {!isLast && (
                          <span className="mt-1 mb-1 w-px flex-1 bg-[color:var(--border)]" aria-hidden="true" />
                        )}
                      </div>
                      <p className={`text-sm leading-relaxed text-[color:var(--text-muted)] ${isLast ? "" : "pb-4"}`}>
                        {step}
                      </p>
                    </li>
                  );
                })}
              </ol>
            </div>

            {/* Code block */}
            <div className="flex flex-col">
              <div className="flex items-center justify-between gap-2 border-b table-rule px-4 py-2.5">
                <p className="mono-text text-[0.68rem] text-[color:var(--text-soft)]">{client.codeLabel}</p>
                <button
                  onClick={() => copy(`code-${client.key}`, client.code)}
                  className={`flex items-center gap-1.5 rounded px-2 py-1 text-[0.68rem] transition-colors ${
                    copied === `code-${client.key}`
                      ? "text-[color:var(--success)]"
                      : "text-[color:var(--text-soft)] hover:bg-[color:var(--surface-strong)] hover:text-[color:var(--text)]"
                  }`}
                  aria-label="Copy code"
                >
                  {copied === `code-${client.key}` ? (
                    <><Check size={11} /> Copied</>
                  ) : (
                    <><Copy size={11} /> Copy</>
                  )}
                </button>
              </div>
              <pre className="mono-panel flex-1 rounded-none rounded-b-[7px] lg:rounded-b-none lg:rounded-br-[7px] overflow-x-auto p-5 text-xs leading-relaxed">{client.code}</pre>
            </div>

          </div>
        </div>
      </section>

      {/* ── Bottom: Checklist + Verify ── */}
      <section className="grid gap-4 lg:grid-cols-2">

        <article className="surface-card p-5">
          <div className="flex items-center gap-2.5">
            <ShieldCheck size={14} className="shrink-0 text-[color:var(--success)]" />
            <p className="text-sm text-[color:var(--text)]">Pre-flight checklist</p>
          </div>
          <ul className="mt-4 space-y-3" role="list">
            {[
              "Platform service is running on the URL above.",
              "Bearer token is present in the selected client.",
              "Wallet balance can cover the first tool calls.",
              "Third-party credentials are loaded by the platform, not the client.",
            ].map((item) => (
              <li key={item} className="flex gap-2.5 text-[0.82rem] leading-relaxed text-[color:var(--text-muted)]">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[color:var(--success)]" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </article>

        <article className="surface-card-light p-5">
          <div className="flex items-center gap-2.5">
            <Zap size={14} className="shrink-0 text-[color:var(--accent)]" />
            <p className="text-sm text-[color:var(--text)]">Demo critical path</p>
          </div>
          <div className="mt-4 space-y-0">
            {verificationSteps.map((step, i) => {
              const isLast = i === verificationSteps.length - 1;
              return (
                <div key={step.label} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${step.tone}`} aria-hidden="true" />
                    {!isLast && <span className="mt-1 mb-1 w-px flex-1 bg-[color:var(--border)]" aria-hidden="true" />}
                  </div>
                  <div className={`min-w-0 ${isLast ? "" : "pb-3.5"}`}>
                    <div className="flex flex-wrap items-baseline gap-2">
                      <p className="text-[0.78rem] text-[color:var(--text)]">{step.label}</p>
                      <p className="mono-text text-[0.62rem] text-[color:var(--accent)]">{step.command}</p>
                    </div>
                    <p className="mt-0.5 text-[0.72rem] leading-relaxed text-[color:var(--text-soft)]">{step.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-5 border-t table-rule pt-4">
            <Link
              href="/feed"
              className="flex items-center gap-1.5 text-[0.78rem] text-[color:var(--text-muted)] transition-colors hover:text-[color:var(--text)]"
            >
              Watch the live feed
              <ArrowRight size={11} />
            </Link>
          </div>
        </article>

      </section>
    </section>
  );
}

