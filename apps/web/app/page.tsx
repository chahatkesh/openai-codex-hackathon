"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  Code2,
  DatabaseZap,
  FileCode2,
  Network,
  Radio,
  ShieldCheck,
  Sparkles,
  WalletCards,
  Workflow,
} from "lucide-react";
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
  { label: "tools/list", detail: "Registry returned", color: "bg-[color:var(--read)]" },
  { label: "wallet", detail: "Spend approved", color: "bg-[color:var(--grep)]" },
  { label: "tools/call", detail: "Provider routed", color: "bg-[color:var(--thinking)]" },
  { label: "integrate", detail: "Gap queued", color: "bg-[color:var(--edit)]" },
];

const proofPoints = [
  { label: "Codex connection", value: "MCP SSE" },
  { label: "Critical tools", value: "scrape / email / sms" },
  { label: "Missing-tool path", value: "bounded pipeline" },
];

const platformCards = [
  {
    title: "Execution That Clears The Gate",
    body: "Every call passes through wallet checks, deterministic routing, and billing logs before the result goes back to Codex.",
    icon: ShieldCheck,
  },
  {
    title: "Catalog That Keeps Moving",
    body: "Published integrations become registry entries that are visible in the frontend and available through tools/list.",
    icon: DatabaseZap,
  },
  {
    title: "Integration Without Theater",
    body: "Discovery, reader, codegen, test/fix, and publish stay bounded so the demo path remains legible.",
    icon: Workflow,
  },
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
    <section className="pb-12">
      <section className="landing-hero border-b table-rule pb-10 pt-8 sm:pb-12 sm:pt-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="mx-auto max-w-4xl text-center"
        >
          <span className="pill bg-[rgba(245,78,0,0.1)] text-[color:var(--accent)]">
            <Sparkles size={12} />
            Agent tool infrastructure
          </span>
          <h1 className="display-title mx-auto mt-6 max-w-4xl text-[color:var(--text)]">Agentic API Marketplace.</h1>
          <p className="body-serif mx-auto mt-5 max-w-2xl">
            FuseKit gives Codex a live tool marketplace, wallet checks before execution, and a request path when a
            capability is missing.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/catalog" className="button-warm button-accent w-full sm:w-auto">
              Browse catalog
              <ArrowRight size={16} />
            </Link>
            <Link href="/integrate" className="button-warm w-full sm:w-auto">
              Request tool
            </Link>
            <Link href="/connect" className="button-warm w-full sm:w-auto">
              Connect Codex
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.08, ease: "easeOut" }}
          className="premium-console mx-auto mt-10 max-w-5xl overflow-hidden"
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[rgba(247,247,244,0.12)] px-4 py-3">
            <div className="flex items-center gap-2">
              <Image src="/window.svg" alt="" width={16} height={16} className="invert" />
              <p className="mono-text text-xs text-[rgba(247,247,244,0.62)]">fusekit.demo.run</p>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-[8px] border border-[rgba(247,247,244,0.12)] px-2.5 py-1 text-xs text-[rgba(247,247,244,0.72)]">
              <Radio size={12} />
              live
            </span>
          </div>

          <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
            <div className="border-b border-[rgba(247,247,244,0.12)] p-5 lg:border-b-0 lg:border-r sm:p-6">
              <div className="mb-5 flex items-center justify-between gap-3">
                <div>
                  <p className="mono-text text-xs text-[color:var(--thinking)]">$ codex tools/list</p>
                  <h2 className="sub-title mt-2 text-[color:var(--surface-light)]">Operational path</h2>
                </div>
                <Image src="/file.svg" alt="" width={30} height={30} className="invert opacity-70" />
              </div>
              <div className="mono-text overflow-x-auto rounded-[8px] border border-[rgba(247,247,244,0.12)] bg-[rgba(247,247,244,0.04)] p-4 text-xs leading-6">
                <p className="text-[color:var(--grep)]">wallet.check: approved</p>
                <p>tool.route: scrape_url</p>
                <p>billing.debit: 2 credits</p>
                <p className="mt-3 text-[color:var(--read)]">tool.result: returned html summary</p>
                <p>ledger.write: execution_log.created</p>
                <p className="mt-3 text-[color:var(--edit)]">missing_tool: TOOL_NOT_FOUND</p>
                <p>integrator.queue: discovery -&gt; publish</p>
              </div>
            </div>

            <div className="bg-[rgba(247,247,244,0.04)] p-5 sm:p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="mono-text text-xs text-[rgba(247,247,244,0.54)]">demo critical path</p>
                  <h3 className="title-small mt-2 text-[color:var(--surface-light)]">Ready for execution</h3>
                </div>
                <Image src="/globe.svg" alt="" width={30} height={30} className="invert opacity-70" />
              </div>
              <div className="mt-5 space-y-3">
                {operationSteps.map((step, index) => (
                  <div key={step.label} className="flex items-center gap-3">
                    <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${step.color} mono-text text-[11px] text-[color:var(--text)]`}>
                      {index + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="mono-text truncate text-xs text-[color:var(--surface-light)]">{step.label}</p>
                      <p className="text-sm text-[rgba(247,247,244,0.56)]">{step.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      <section className="mt-6 grid gap-3 sm:grid-cols-3">
        {proofPoints.map((item) => (
          <article key={item.label} className="surface-card-light p-4">
            <p className="eyebrow">{item.label}</p>
            <p className="mt-2 text-sm text-[color:var(--text)]">{item.value}</p>
          </article>
        ))}
      </section>

      {stats || isLoaded ? (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="mt-8">
          {stats ? <StatsBar stats={stats} /> : null}
          {statsError ? <p className="surface-card-light mt-4 p-3 text-sm text-[color:var(--gold)]">{statsError}</p> : null}
        </motion.div>
      ) : null}

      <section className="mt-10 grid gap-4 lg:grid-cols-3">
        {platformCards.map((card) => {
          const Icon = card.icon;
          return (
            <article key={card.title} className="surface-card p-5">
              <span className="flex h-10 w-10 items-center justify-center rounded-[8px] border table-rule bg-[color:var(--surface-light)] text-[color:var(--accent)]">
                <Icon size={19} />
              </span>
              <h2 className="title-small mt-5 text-[color:var(--text)]">{card.title}</h2>
              <p className="body-serif mt-3">{card.body}</p>
            </article>
          );
        })}
      </section>

      <section className="mt-10 space-y-5">
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
              <FileCode2 className="mb-3 h-8 w-8 text-[color:var(--text-soft)]" />
              <h3 className="title-small text-[color:var(--text)]">No tools published yet</h3>
              <p className="body-serif mt-2 max-w-sm">Trigger an integration to fill the catalog with callable tools.</p>
            </div>
          )
        )}
      </section>

      <section className="mt-10 surface-card-light flex flex-wrap items-center justify-between gap-4 p-5">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-1 h-5 w-5 shrink-0 text-[color:var(--success)]" />
          <div>
            <h2 className="title-small text-[color:var(--text)]">Demo path stays intact.</h2>
            <p className="body-serif mt-1">Connect Codex, execute critical tools, deduct credits, and publish new capabilities.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/wallet" className="button-warm">
            View wallet
            <WalletCards size={16} />
          </Link>
          <Link href="/connect" className="button-warm">
            MCP setup
            <Network size={16} />
          </Link>
        </div>
      </section>
    </section>
  );
}
