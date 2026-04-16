"use client";

import type { CatalogItem } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { motion } from "framer-motion";

type Props = {
  tools: CatalogItem[];
};

export function CatalogTable({ tools }: Props) {
  return (
    <div className="surface-card-light overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b table-rule bg-[color:var(--surface)] text-xs text-[color:var(--text-muted)]">
          <tr>
            <th className="px-5 py-4 font-medium">Name</th>
            <th className="px-5 py-4 font-medium">Provider</th>
            <th className="px-5 py-4 font-medium">Category</th>
            <th className="px-5 py-4 font-medium">Cost</th>
            <th className="px-5 py-4 text-right font-medium">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[rgba(38,37,30,0.1)]">
          {tools.map((tool) => (
            <motion.tr
              key={tool.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="group transition-colors hover:bg-[color:var(--surface)]"
            >
              <td className="px-5 py-4">
                <p className="font-medium text-[color:var(--text)] transition-colors group-hover:text-[color:var(--accent)]">{tool.name}</p>
                <p className="mt-1 max-w-md text-xs leading-relaxed text-[color:var(--text-muted)]">{tool.description}</p>
              </td>
              <td className="px-5 py-4 text-[color:var(--text-muted)]">{tool.provider}</td>
              <td className="px-5 py-4 text-[color:var(--text-muted)]">
                <span className="pill">{tool.category ?? "other"}</span>
              </td>
              <td className="px-5 py-4">
                <span className="mono-text text-xs text-[color:var(--accent)]">{tool.cost_per_call} cr</span>
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
