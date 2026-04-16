"use client";

import type { CatalogItem } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { motion } from "framer-motion";

type Props = {
  tools: CatalogItem[];
};

export function CatalogTable({ tools }: Props) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-white/5 bg-[color:var(--surface)] shadow-lg shadow-teal-500/5">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-white/5 bg-white/5 text-xs uppercase tracking-[0.15em] text-slate-400 font-semibold">
          <tr>
            <th className="px-5 py-4">Name</th>
            <th className="px-5 py-4">Provider</th>
            <th className="px-5 py-4">Category</th>
            <th className="px-5 py-4">Cost</th>
            <th className="px-5 py-4 text-right">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {tools.map((tool) => (
            <motion.tr 
              key={tool.id} 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="group transition-colors hover:bg-white/[0.03]"
            >
              <td className="px-5 py-4">
                <p className="font-semibold text-slate-200 group-hover:text-teal-300 transition-colors">{tool.name}</p>
                <p className="mt-1 text-xs text-slate-400 max-w-sm font-medium">{tool.description}</p>
              </td>
              <td className="px-5 py-4 text-slate-400">{tool.provider}</td>
              <td className="px-5 py-4 text-slate-400">
                <span className="rounded-full bg-white/5 border border-white/5 px-2.5 py-1 text-xs">{tool.category ?? "other"}</span>
              </td>
              <td className="px-5 py-4">
                <span className="font-medium text-teal-200">{tool.cost_per_call} cr</span>
              </td>
              <td className="px-5 py-4 text-right">
                <StatusBadge status={tool.status} />
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
