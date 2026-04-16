"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Zap, Code2, Network, ChevronRight } from "lucide-react";
import {
  EndpointUnavailableError,
  type CatalogItem,
  type CatalogStats,
  getCatalogStats,
  getRecentTools,
} from "@/lib/api";
import { StatsBar } from "@/components/StatsBar";
import { ToolCard } from "@/components/ToolCard";

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
        setStatsError("Stats endpoint unavailable. Showing static landing content.");
      }

      try {
        setRecentTools(await getRecentTools());
        setRecentError(null);
      } catch (error) {
        if (error instanceof EndpointUnavailableError) {
          setRecentError("Recent tools endpoint unavailable. Catalog still works.");
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
    <section className="space-y-12 pb-12">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br from-[color:var(--surface-strong)] to-[color:var(--surface)] p-8 sm:p-12 shadow-2xl"
      >
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay"></div>
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-teal-500 blur-[100px] opacity-20"></div>
        
        <div className="relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 rounded-full border border-teal-500/30 bg-teal-500/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-teal-300 backdrop-blur-sm"
          >
            <Zap size={14} className="fill-teal-400" /> V1 Engine Live
          </motion.div>
          
          <h1 className="mt-6 max-w-3xl text-4xl font-bold tracking-tight text-white sm:text-6xl lg:leading-[1.1]">
            The <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-300 to-cyan-500">API execution layer</span> for the agentic era.
          </h1>
          
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-slate-400 sm:text-lg">
            Codex connects through MCP, executes tools with integrated wallet enforcement, and dynamically triggers self-integrations when tools are missing. 
          </p>
          
          <div className="mt-10 flex flex-wrap gap-4">
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link href="/catalog" className="group flex items-center gap-2 rounded-xl bg-teal-400 px-6 py-3.5 text-sm font-bold text-slate-900 shadow-lg shadow-teal-500/25 transition-all hover:bg-teal-300 hover:shadow-teal-500/40">
                Browse Catalog
                <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
              </Link>
            </motion.div>
            
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              <Link href="/connect" className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur-md transition-all hover:bg-white/10 hover:border-white/20">
                <Network size={16} />
                Connect Codex
              </Link>
            </motion.div>
          </div>
        </div>
      </motion.div>

      {stats || isLoaded ? (
        <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ duration: 0.5, delay: 0.3 }}
        >
          {stats && <StatsBar stats={stats} />}
          {statsError ? <p className="mt-4 text-sm font-medium text-amber-400/80 bg-amber-500/10 px-4 py-2 rounded-lg border border-amber-500/20">{statsError}</p> : null}
        </motion.div>
      ) : null}

      <section className="space-y-6 relative z-10">
        <div className="flex items-end justify-between border-b border-white/5 pb-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Code2 className="text-teal-400" />
              Recently Added Tools
            </h2>
            <p className="mt-1 text-sm text-slate-400">Discover zero-setup API capabilities</p>
          </div>
          <Link href="/feed" className="group flex items-center gap-1 text-sm font-semibold text-teal-400 transition-colors hover:text-teal-300">
            Live Feed <ChevronRight size={16} className="transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
        
        {recentError ? (
          <p className="text-sm font-medium text-amber-400/80 bg-amber-500/10 px-4 py-3 rounded-xl border border-amber-500/20 shadow-sm">{recentError}</p>
        ) : null}
        
        {recentTools.length ? (
          <motion.div 
            initial="hidden"
            animate="visible"
            variants={{
              visible: { transition: { staggerChildren: 0.1 } }
            }}
            className="grid gap-5 md:grid-cols-2 lg:grid-cols-2"
          >
            {recentTools.slice(0, 4).map((tool) => (
              <motion.div 
                key={tool.id}
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 }
                }}
              >
                <div className="h-full">
                  <ToolCard tool={tool} />
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          isLoaded && !recentError && (
             <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-[color:var(--surface)]/50 py-16 px-4 text-center backdrop-blur-sm">
                <div className="rounded-full bg-white/5 p-4 mb-4">
                  <Code2 className="h-8 w-8 text-slate-500" />
                </div>
                <h3 className="text-lg font-semibold text-slate-200">No tools found</h3>
                <p className="mt-2 max-w-sm text-sm text-slate-400">
                  Waiting for integrated tools to appear. Trigger a new integration to fill the catalog.
                </p>
             </div>
          )
        )}
      </section>
    </section>
  );
}
