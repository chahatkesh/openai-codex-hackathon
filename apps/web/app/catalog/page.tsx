"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CatalogTable } from "@/components/CatalogTable";
import { ToolCard } from "@/components/ToolCard";
import type { CatalogItem } from "@/lib/api";
import { getCatalog } from "@/lib/api";

const STATUS_FILTERS = ["all", "live", "pending_credentials", "deprecated"];
const CATEGORY_FILTERS = ["all", "communication", "data_retrieval", "search", "payments", "productivity", "other"];

export default function CatalogPage() {
  const [tools, setTools] = useState<CatalogItem[]>([]);
  const [status, setStatus] = useState("all");
  const [category, setCategory] = useState("all");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const next = await getCatalog({
          status: status === "all" ? undefined : status,
          category: category === "all" ? undefined : category,
        });
        setTools(next);
        setError(null);
      } catch {
        setError("Catalog endpoint unavailable. Retrying automatically.");
      }
    };

    load();
    const timer = window.setInterval(load, 5000);
    return () => window.clearInterval(timer);
  }, [status, category]);

  return (
    <section className="space-y-6 pb-12">
      <header className="surface-card-light p-6">
        <p className="eyebrow">Tool registry</p>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="section-title text-[color:var(--text)]">Catalog</h1>
            <p className="body-serif mt-2 max-w-2xl">
              Browse every tool currently available to Codex. New integrations appear here after publish.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="pill bg-[rgba(245,78,0,0.1)] text-[color:var(--accent)]">{tools.length} visible</span>
            <Link href="/credentials" className="warm-link text-sm underline">
              Manage provider credentials
            </Link>
          </div>
        </div>
      </header>

      <div className="surface-card grid gap-4 p-4 md:grid-cols-2">
        <label className="text-sm text-[color:var(--text-muted)]">
          Status
          <select value={status} onChange={(event) => setStatus(event.target.value)} className="input-warm mt-2">
            {STATUS_FILTERS.map((item) => (
              <option key={item} value={item}>
                {item.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-[color:var(--text-muted)]">
          Category
          <select value={category} onChange={(event) => setCategory(event.target.value)} className="input-warm mt-2">
            {CATEGORY_FILTERS.map((item) => (
              <option key={item} value={item}>
                {item.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{error}</p> : null}

      <div className="hidden lg:block">
        <CatalogTable tools={tools} />
      </div>
      <div className="grid gap-4 lg:hidden">
        {tools.map((tool) => (
          <ToolCard key={tool.id} tool={tool} />
        ))}
      </div>

      {!tools.length && !error ? (
        <p className="surface-card-light p-4 text-sm text-[color:var(--text-muted)]">No tools match the current filters yet.</p>
      ) : null}
    </section>
  );
}
