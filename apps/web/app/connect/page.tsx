import Image from "next/image";
import { apiBaseUrl } from "@/lib/api";

const endpoint = `${apiBaseUrl}/mcp/http`;
const demoToken = "demo-token-fusekit-2026";

export default function ConnectPage() {
  return (
    <section className="space-y-6 pb-12">
      <header className="surface-card-light p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="eyebrow">Codex connection</p>
            <h1 className="section-title mt-3 text-[color:var(--text)]">Connect Codex</h1>
            <p className="body-serif mt-2 max-w-2xl">Add the FuseKit MCP endpoint, attach the demo token, and verify discovery with tools/list.</p>
          </div>
          <Image src="/globe.svg" alt="" width={36} height={36} className="mt-1 opacity-60" />
        </div>
      </header>

      <ol className="surface-card grid gap-3 p-5 text-sm text-[color:var(--text-muted)] md:grid-cols-4">
        <li className="border-b table-rule pb-3 md:border-b-0 md:border-r md:pb-0 md:pr-3">1. Open Codex MCP settings and add a new MCP server.</li>
        <li className="border-b table-rule pb-3 md:border-b-0 md:border-r md:pb-0 md:pr-3">2. Set endpoint URL to the FuseKit MCP HTTP URL shown below.</li>
        <li className="border-b table-rule pb-3 md:border-b-0 md:border-r md:pb-0 md:pr-3">3. Add the demo token as bearer auth (hackathon mode).</li>
        <li>4. Save and run tools/list to verify tool discovery.</li>
      </ol>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="surface-card-light p-5">
          <p className="eyebrow">MCP endpoint</p>
          <code className="mono-panel mt-3 block overflow-x-auto p-3 text-sm">{endpoint}</code>
        </article>

        <article className="surface-card-light p-5">
          <p className="eyebrow">Demo auth token</p>
          <code className="mono-panel mt-3 block overflow-x-auto p-3 text-sm">{demoToken}</code>
        </article>
      </section>

      <section className="surface-card p-5">
        <p className="eyebrow">Example configuration</p>
        <pre className="mono-panel mt-3 overflow-x-auto p-4 text-sm leading-relaxed">
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
