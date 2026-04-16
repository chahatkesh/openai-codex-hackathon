"use client";

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
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold text-white">Catalog</h1>
        <p className="mt-2 text-sm text-[color:var(--text-muted)]">
          Browse every tool currently available to Codex. New tools appear automatically after integration publishes.
        </p>
      </header>

      <div className="grid gap-3 rounded-xl border border-white/10 bg-[color:var(--surface)] p-4 md:grid-cols-2">
        <label className="text-sm text-[color:var(--text-muted)]">
          Status
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="mt-2 w-full rounded-lg border border-white/15 bg-slate-900/80 px-3 py-2 text-sm text-white"
          >
            {STATUS_FILTERS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-[color:var(--text-muted)]">
          Category
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="mt-2 w-full rounded-lg border border-white/15 bg-slate-900/80 px-3 py-2 text-sm text-white"
          >
            {CATEGORY_FILTERS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="text-sm text-amber-200">{error}</p> : null}

      <div className="hidden lg:block">
        <CatalogTable tools={tools} />
      </div>
      <div className="grid gap-4 lg:hidden">
        {tools.map((tool) => (
          <ToolCard key={tool.id} tool={tool} />
        ))}
      </div>

      {!tools.length && !error ? (
        <p className="rounded-xl border border-white/10 bg-[color:var(--surface)] p-4 text-sm text-[color:var(--text-muted)]">
          No tools match the current filters yet.
        </p>
      ) : null}
    </section>
  );
}
