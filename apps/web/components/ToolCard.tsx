"use client";

import type { CatalogItem } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { motion } from "framer-motion";
import { Building2, Coins, Tag, Wrench } from "lucide-react";

type Props = {
  tool: CatalogItem;
};

export function ToolCard({ tool }: Props) {
  return (
    <motion.article
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
      className="surface-card ambient-card flex h-full flex-col justify-between p-5"
    >
      <div>
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] border table-rule bg-[color:var(--surface-light)] text-[color:var(--accent)]">
              <Wrench size={18} strokeWidth={1.6} />
            </span>
            <h3 className="title-small min-w-0 break-words text-[color:var(--text)]">{tool.name}</h3>
          </div>
          <StatusBadge status={tool.status} />
        </div>
        <p className="body-serif mb-6">{tool.description}</p>
      </div>

      <div className="mt-auto flex flex-wrap items-center gap-2">
        <span className="pill">
          <Building2 size={12} />
          {tool.provider}
        </span>
        {tool.category ? (
          <span className="pill">
            <Tag size={12} />
            {tool.category}
          </span>
        ) : null}
        <span className="pill bg-[color:var(--surface-light)] text-[color:var(--text)]">
          <Coins size={12} />
          {tool.cost_per_call} credits
        </span>
      </div>
    </motion.article>
  );
}
