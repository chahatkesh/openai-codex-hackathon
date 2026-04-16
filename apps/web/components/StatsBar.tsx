"use client";

import type { ReactNode } from "react";
import type { CatalogStats } from "@/lib/api";
import { motion } from "framer-motion";
import { CopySlash, KeyRound, PlayCircle } from "lucide-react";

type Props = {
  stats: CatalogStats;
};

export function StatsBar({ stats }: Props) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <StatCard label="Total tools" value={stats.total} icon={<CopySlash size={16} />} delay={0.05} />
      <StatCard label="Live tools" value={stats.live} icon={<PlayCircle size={16} />} delay={0.1} />
      <StatCard label="Need credentials" value={stats.pending_credentials} icon={<KeyRound size={16} />} delay={0.15} />
    </div>
  );
}

function StatCard({ label, value, icon, delay }: { label: string; value: number; icon: ReactNode; delay: number }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay }}
      whileHover={{ y: -2 }}
      className="surface-card ambient-card p-5"
    >
      <div className="flex items-center gap-2 text-sm text-[color:var(--text-muted)]">
        <span className="text-[color:var(--accent)]">{icon}</span>
        {label}
      </div>
      <p className="mt-4 text-4xl font-normal leading-none text-[color:var(--text)]">{value}</p>
    </motion.article>
  );
}
