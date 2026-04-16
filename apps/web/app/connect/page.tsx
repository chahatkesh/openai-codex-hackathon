import { apiBaseUrl } from "@/lib/api";

const endpoint = `${apiBaseUrl}/mcp/http`;
const demoToken = "demo-token-fusekit-2026";

export default function ConnectPage() {
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold text-white">Connect Codex</h1>
        <p className="mt-2 text-sm text-[color:var(--text-muted)]">
          Use this setup to connect Codex to FuseKit in under a minute.
        </p>
      </header>

      <ol className="space-y-3 rounded-xl border border-white/10 bg-[color:var(--surface)] p-5 text-sm text-[color:var(--text-muted)]">
        <li>1. Open Codex MCP settings and add a new MCP server.</li>
        <li>2. Set endpoint URL to the FuseKit MCP HTTP URL shown below.</li>
        <li>3. Add the demo token as bearer auth (hackathon mode).</li>
        <li>4. Save and run `tools/list` to verify tool discovery.</li>
      </ol>

      <section className="space-y-3 rounded-xl border border-white/10 bg-[color:var(--surface)] p-5">
        <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">MCP Endpoint</p>
        <code className="block overflow-x-auto rounded-lg bg-slate-900/80 p-3 text-sm text-cyan-200">{endpoint}</code>
      </section>

      <section className="space-y-3 rounded-xl border border-white/10 bg-[color:var(--surface)] p-5">
        <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">Demo Auth Token</p>
        <code className="block overflow-x-auto rounded-lg bg-slate-900/80 p-3 text-sm text-cyan-200">{demoToken}</code>
      </section>

      <section className="space-y-3 rounded-xl border border-white/10 bg-[color:var(--surface)] p-5">
        <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">Example Configuration</p>
        <pre className="overflow-x-auto rounded-lg bg-slate-900/80 p-3 text-sm text-cyan-200">
{`{
  "type": "http",
  "url": "${endpoint}",
  "headers": {
    "Authorization": "Bearer ${demoToken}"
  }
}`}
        </pre>
      </section>
    </section>
  );
}
