"use client";

import type { CatalogStats } from "@/lib/api";
import { motion } from "framer-motion";
import { CopySlash, PlayCircle, KeyRound } from "lucide-react";

type Props = {
  stats: CatalogStats;
};

export function StatsBar({ stats }: Props) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <StatCard label="Total Tools" value={stats.total} icon={<CopySlash size={16} />} delay={0.1} />
      <StatCard label="Live Tools" value={stats.live} icon={<PlayCircle size={16} />} delay={0.2} />
      <StatCard label="Pending Credentials" value={stats.pending_credentials} icon={<KeyRound size={16} />} delay={0.3} />
    </div>
  );
}

function StatCard({ label, value, icon, delay }: { label: string; value: number; icon: React.ReactNode; delay: number }) {
  return (
    <motion.article 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ y: -4, scale: 1.02 }}
      className="group relative overflow-hidden rounded-2xl border border-white/5 bg-[color:var(--surface)] p-6 shadow-md transition-shadow hover:shadow-lg hover:shadow-teal-500/10"
    >
      <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-teal-500/5 blur-2xl transition-all group-hover:bg-teal-500/10"></div>
      
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        <span className="text-teal-500/70">{icon}</span>
        {label}
      </div>
      <p className="mt-4 text-4xl font-bold tracking-tight text-white drop-shadow-sm">{value}</p>
    </motion.article>
  );
}
