"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Check,
  CheckCircle2,
  Code2,
  Copy,
  FileCode2,
  Network,
  ShieldCheck,
  WalletCards,
  Workflow,
} from "lucide-react";
import { apiBaseUrl } from "@/lib/api";

const endpoint = `${apiBaseUrl}/mcp/http`;
const demoToken = "demo-token-fusekit-2026";

const credentials = [
  { key: "transport", label: "Transport", value: "Streamable HTTP", copyable: false },
  { key: "url", label: "Server URL", value: endpoint, copyable: true },
  { key: "token", label: "Bearer Token", value: demoToken, copyable: true },
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
      "Open the Command Palette and add an MCP server.",
      "Choose HTTP transport and name the server fusekit.",
      "Paste the endpoint and bearer token.",
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
      "Use bearer token auth with the demo token below.",
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
    detail: "Confirm scrape_url, send_email, and send_sms are visible.",
    tone: "bg-[color:var(--read)]",
  },
  {
    label: "Execute",
    command: "tools/call",
    detail: "Run scrape_url first, then send_email or send_sms.",
    tone: "bg-[color:var(--grep)]",
  },
  {
    label: "Spend",
    command: "wallet.check",
    detail: "Each call passes wallet checks before the platform routes.",
    tone: "bg-[color:var(--thinking)]",
  },
  {
    label: "Grow",
    command: "TOOL_NOT_FOUND",
    detail: "Ask for a missing tool and watch the pipeline publish it.",
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
    <section className="pb-16">

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
          <Link href="/wallet" className="button-warm shrink-0">
            Check wallet
            <WalletCards size={15} />
          </Link>
        </div>
      </header>

      {/* ── Credentials strip ── */}
      <div
        className="mt-6 grid gap-px overflow-hidden rounded-[8px] border table-rule bg-[color:var(--border)] md:grid-cols-3"
        aria-label="Connection credentials"
      >
        {credentials.map((cred) => (
          <div key={cred.key} className="flex items-start justify-between gap-3 bg-[color:var(--surface-light)] px-4 py-3.5">
            <div className="min-w-0">
              <p className="eyebrow">{cred.label}</p>
              <p className="mono-text mt-1.5 break-all text-xs leading-relaxed text-[color:var(--text)]">
                {cred.value}
              </p>
            </div>
            {cred.copyable && (
              <button
                onClick={() => copy(cred.key, cred.value)}
                className="mt-0.5 shrink-0 rounded p-1.5 text-[color:var(--text-soft)] transition-colors hover:bg-[color:var(--surface-strong)] hover:text-[color:var(--text)]"
                aria-label={`Copy ${cred.label}`}
                title={`Copy ${cred.label}`}
              >
                {copied === cred.key ? <Check size={13} /> : <Copy size={13} />}
              </button>
            )}
          </div>
        ))}
      </div>

      {/* ── Client tabs ── */}
      <section className="mt-10" aria-label="Client setup">

        {/* Tab strip */}
        <div
          className="flex gap-0.5 border-b table-rule"
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
                className={`relative flex items-center gap-2 px-4 pb-3 pt-2 text-sm transition-colors ${
                  active
                    ? "text-[color:var(--text)]"
                    : "text-[color:var(--text-soft)] hover:text-[color:var(--text-muted)]"
                }`}
              >
                <Icon size={14} />
                {c.label}
                {active && (
                  <span className="absolute bottom-0 left-0 right-0 h-px bg-[color:var(--text)]" aria-hidden="true" />
                )}
              </button>
            );
          })}
        </div>

        {/* Tab panel */}
        <div role="tabpanel" className="mt-6 grid gap-6 lg:grid-cols-[1fr_1.2fr]">

          {/* Steps */}
          <div>
            <div className="flex items-center gap-3">
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-[6px] ${client.tone}`}
                aria-hidden="true"
              >
                <ClientIcon size={16} />
              </span>
              <div>
                <p className="eyebrow">{client.eyebrow}</p>
                <p className="mt-0.5 text-sm text-[color:var(--text)]">{client.label}</p>
              </div>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-[color:var(--text-muted)]">{client.summary}</p>
            <ol className="mt-5 space-y-2.5" aria-label={`${client.label} setup steps`}>
              {client.steps.map((step, i) => (
                <li key={step} className="flex gap-3 text-sm leading-relaxed text-[color:var(--text-muted)]">
                  <span className="mono-text mt-px shrink-0 text-[0.65rem] text-[color:var(--text-soft)]">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </div>

          {/* Code block */}
          <div>
            <div className="flex items-center justify-between gap-2 border-b table-rule pb-2.5">
              <p className="eyebrow">{client.codeLabel}</p>
              <button
                onClick={() => copy(`code-${client.key}`, client.code)}
                className="flex items-center gap-1.5 rounded px-2 py-1 text-[0.68rem] text-[color:var(--text-soft)] transition-colors hover:bg-[color:var(--surface-strong)] hover:text-[color:var(--text)]"
                aria-label="Copy code"
              >
                {copied === `code-${client.key}` ? (
                  <><Check size={11} /> Copied</>
                ) : (
                  <><Copy size={11} /> Copy</>
                )}
              </button>
            </div>
            <pre className="mono-panel mt-3 max-h-72 overflow-x-auto p-4 text-xs leading-relaxed">{client.code}</pre>
          </div>

        </div>
      </section>

      {/* ── Bottom: Checklist + Verify ── */}
      <section className="mt-10 grid gap-4 lg:grid-cols-2">

        <article className="surface-card p-5">
          <div className="flex items-center gap-2.5">
            <ShieldCheck size={15} className="shrink-0 text-[color:var(--success)]" />
            <div>
              <p className="eyebrow">Before the demo</p>
              <p className="mt-0.5 text-sm text-[color:var(--text)]">Connection checklist</p>
            </div>
          </div>
          <ul className="mt-4 space-y-2.5" role="list">
            {[
              "Platform service is running on the URL above.",
              "Bearer token is present in the selected client.",
              "Wallet balance can cover the first tool calls.",
              "Third-party credentials are loaded by the platform, not the client.",
            ].map((item) => (
              <li key={item} className="flex gap-2.5 text-sm leading-relaxed text-[color:var(--text-muted)]">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[color:var(--success)]" aria-hidden="true" />
                {item}
              </li>
            ))}
          </ul>
        </article>

        <article className="surface-card-light p-5">
          <div className="flex items-center gap-2.5">
            <Workflow size={15} className="shrink-0 text-[color:var(--accent)]" />
            <div>
              <p className="eyebrow">Verify the path</p>
              <p className="mt-0.5 text-sm text-[color:var(--text)]">Run the same checks everywhere</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-4">
            {verificationSteps.map((step) => (
              <div key={step.label}>
                <div className="flex items-center gap-2">
                  <span className={`h-2 w-2 shrink-0 rounded-full ${step.tone}`} aria-hidden="true" />
                  <p className="text-xs text-[color:var(--text)]">{step.label}</p>
                </div>
                <p className="mono-text mt-1 text-[0.65rem] text-[color:var(--accent)]">{step.command}</p>
                <p className="mt-1 text-xs leading-relaxed text-[color:var(--text-muted)]">{step.detail}</p>
              </div>
            ))}
          </div>
        </article>

      </section>
    </section>
  );
}

