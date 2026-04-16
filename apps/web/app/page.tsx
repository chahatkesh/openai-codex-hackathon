"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Code2, DatabaseZap, Network, Radio, WalletCards } from "lucide-react";
import {
  EndpointUnavailableError,
  type CatalogItem,
  type CatalogStats,
  getCatalogStats,
  getRecentTools,
} from "@/lib/api";
import { StatsBar } from "@/components/StatsBar";
import { ToolCard } from "@/components/ToolCard";

const operationSteps = [
  { label: "tools/list", detail: "Catalog read", color: "bg-[color:var(--read)]" },
  { label: "wallet", detail: "Balance checked", color: "bg-[color:var(--grep)]" },
  { label: "tools/call", detail: "Execution routed", color: "bg-[color:var(--thinking)]" },
  { label: "integrate", detail: "Missing tool queued", color: "bg-[color:var(--edit)]" },
];

export default function Home() {
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [recentTools, setRecentTools] = useState<CatalogItem[]>([]);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [recentError, setRecentError] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setStats(await getCatalogStats());
        setStatsError(null);
      } catch {
        setStatsError("Stats endpoint unavailable. Showing the demo shell.");
      }

      try {
        setRecentTools(await getRecentTools());
        setRecentError(null);
      } catch (error) {
        if (error instanceof EndpointUnavailableError) {
          setRecentError("Recent tools endpoint unavailable. Catalog polling will resume automatically.");
        } else {
          setRecentError("Could not load recent tools right now.");
        }
      }
      setIsLoaded(true);
    };

    load();
    const timer = window.setInterval(load, 8000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="space-y-10 pb-12">
      <div className="grid gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="surface-card-light elevated-card p-6 sm:p-8"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="pill bg-[rgba(245,78,0,0.1)] text-[color:var(--accent)]">
              <Radio size={12} />
              V1 engine live
            </span>
            <span className="pill">MCP ready</span>
          </div>

          <h1 className="display-title mt-7 max-w-3xl text-[color:var(--text)]">Marketplace console for agent tools.</h1>
          <p className="body-serif mt-5 max-w-2xl">
            Codex reaches FuseKit through MCP, lists callable tools, checks wallet rules before execution, and queues a bounded
            integration whenever the missing-tool path is hit.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/catalog" className="button-warm button-accent">
              Browse catalog
              <ArrowRight size={16} />
            </Link>
            <Link href="/integrate" className="button-warm">
              Request an API
            </Link>
            <Link href="/connect" className="button-warm">
              Connect Codex
            </Link>
          </div>

          <div className="mt-8 grid gap-3 border-t table-rule pt-5 sm:grid-cols-3">
            <div className="flex items-start gap-2">
              <Network size={17} className="mt-1 shrink-0 text-[color:var(--accent)]" />
              <p className="text-sm text-[color:var(--text-muted)]">SSE MCP endpoint for Codex</p>
            </div>
            <div className="flex items-start gap-2">
              <WalletCards size={17} className="mt-1 shrink-0 text-[color:var(--accent)]" />
              <p className="text-sm text-[color:var(--text-muted)]">Pre-call deductions and limits</p>
            </div>
            <div className="flex items-start gap-2">
              <DatabaseZap size={17} className="mt-1 shrink-0 text-[color:var(--accent)]" />
              <p className="text-sm text-[color:var(--text-muted)]">Published tools update catalog</p>
            </div>
          </div>
        </motion.section>

        <motion.aside
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.08, ease: "easeOut" }}
          className="surface-card p-4 sm:p-5"
        >
          <div className="flex items-center justify-between border-b table-rule pb-3">
            <div className="flex items-center gap-2">
              <Image src="/window.svg" alt="" width={16} height={16} className="opacity-70" />
              <p className="mono-text text-xs text-[color:var(--text-muted)]">demo-session.mcp</p>
            </div>
            <span className="h-2 w-2 rounded-full bg-[color:var(--success)]" aria-hidden="true" />
          </div>

          <div className="mono-panel mt-4 overflow-hidden p-4 text-xs leading-6">
            <p className="text-[color:var(--thinking)]">$ codex tools/list</p>
            <p>scrape_url / send_email / send_sms</p>
            <p className="mt-3 text-[color:var(--grep)]">$ tools/call scrape_url</p>
            <p>wallet.check: approved</p>
            <p>billing.log: 2 credits deducted</p>
            <p className="mt-3 text-[color:var(--edit)]">$ tools/call missing_tool</p>
            <p>error: TOOL_NOT_FOUND</p>
            <p>integrator.queue: discovery -&gt; publish</p>
          </div>

          <div className="mt-5 space-y-3">
            {operationSteps.map((step, index) => (
              <div key={step.label} className="flex items-center gap-3">
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${step.color} mono-text text-[11px] text-[color:var(--text)]`}>
                  {index + 1}
                </span>
                <div>
                  <p className="mono-text text-xs text-[color:var(--text)]">{step.label}</p>
                  <p className="text-sm text-[color:var(--text-muted)]">{step.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.aside>
      </div>

      {stats || isLoaded ? (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
          {stats ? <StatsBar stats={stats} /> : null}
          {statsError ? (
            <p className="surface-card-light mt-4 p-3 text-sm text-[color:var(--gold)]">{statsError}</p>
          ) : null}
        </motion.div>
      ) : null}

      <section className="space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-3 border-b table-rule pb-4">
          <div>
            <p className="eyebrow">Catalog pulse</p>
            <h2 className="section-title mt-1 flex items-center gap-2 text-[color:var(--text)]">
              <Code2 className="text-[color:var(--accent)]" />
              Recently added tools
            </h2>
          </div>
          <Link href="/feed" className="warm-link text-sm underline">
            Open live feed
          </Link>
        </div>

        {recentError ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{recentError}</p> : null}

        {recentTools.length ? (
          <motion.div
            initial="hidden"
            animate="visible"
            variants={{ visible: { transition: { staggerChildren: 0.06 } } }}
            className="grid gap-4 md:grid-cols-2"
          >
            {recentTools.slice(0, 4).map((tool) => (
              <motion.div
                key={tool.id}
                variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
                className="h-full"
              >
                <ToolCard tool={tool} />
              </motion.div>
            ))}
          </motion.div>
        ) : (
          isLoaded &&
          !recentError && (
            <div className="surface-card-light flex flex-col items-center justify-center px-4 py-14 text-center">
              <Code2 className="mb-3 h-8 w-8 text-[color:var(--text-soft)]" />
              <h3 className="title-small text-[color:var(--text)]">No tools published yet</h3>
              <p className="body-serif mt-2 max-w-sm">Trigger an integration to fill the catalog with callable tools.</p>
            </div>
          )
        )}
      </section>
    </section>
  );
}
