"use client";

import type { CatalogItem } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { motion } from "framer-motion";
import { Wrench, Building2, Tag, Coins } from "lucide-react";

type Props = {
  tool: CatalogItem;
};

export function ToolCard({ tool }: Props) {
  return (
    <motion.article 
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ duration: 0.2 }}
      className="group relative overflow-hidden rounded-2xl border border-white/5 bg-gradient-to-b from-[color:var(--surface)] to-[color:var(--background-soft)] p-5 shadow-lg flex flex-col justify-between h-full"
    >
      <div className="absolute inset-x-0 -top-px h-px w-full bg-gradient-to-r from-transparent via-teal-500/30 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
      
      <div>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-teal-500/10 text-teal-400">
              <Wrench size={20} strokeWidth={1.5} />
            </div>
            <h3 className="text-lg font-semibold text-slate-100">{tool.name}</h3>
          </div>
          <StatusBadge status={tool.status} />
        </div>
        <p className="text-sm text-slate-400 leading-relaxed mb-6">{tool.description}</p>
      </div>

      <div className="mt-auto flex flex-wrap items-center gap-2 text-xs font-medium">
        <div className="flex items-center gap-1.5 rounded-full border border-teal-500/20 bg-teal-500/5 px-2.5 py-1 text-teal-300">
          <Building2 size={12} />
          {tool.provider}
        </div>
        {tool.category ? (
          <div className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-slate-300">
            <Tag size={12} />
            {tool.category}
          </div>
        ) : null}
        <div className="flex items-center gap-1.5 rounded-full border border-teal-400/20 bg-teal-400/10 px-2.5 py-1 text-teal-200">
          <Coins size={12} />
          {tool.cost_per_call} credits
        </div>
      </div>
    </motion.article>
  );
}
