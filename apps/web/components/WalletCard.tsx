"use client";

import type { WalletBalance } from "@/lib/api";
import { motion } from "framer-motion";
import { BadgeInfo, ShieldAlert, Wallet } from "lucide-react";

type Props = {
  balance: WalletBalance;
};

export function WalletCard({ balance }: Props) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="surface-card elevated-card overflow-hidden p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[8px] border table-rule bg-[color:var(--surface-light)] text-[color:var(--accent)]">
            <Wallet size={22} />
          </span>
          <div>
            <p className="eyebrow">Available balance</p>
            <p className="text-sm text-[color:var(--text-muted)]">Wallet checks run before every tool call.</p>
          </div>
        </div>
        <span className="pill bg-[color:var(--surface-light)]">credits ledger</span>
      </div>

      <div className="mt-8 flex flex-wrap items-end gap-3">
        <motion.p
          key={balance.balance}
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="display-title text-[color:var(--text)]"
        >
          {balance.balance.toLocaleString()}
        </motion.p>
        <span className="pb-3 text-base text-[color:var(--text-muted)]">credits</span>
      </div>

      <div className="mt-6 grid gap-4 border-t table-rule pt-5 sm:grid-cols-2">
        <div className="flex items-start gap-3">
          <BadgeInfo size={17} className="mt-0.5 shrink-0 text-[color:var(--accent)]" />
          <div>
            <p className="text-sm text-[color:var(--text-muted)]">Session limit</p>
            <p className="title-small text-[color:var(--text)]">{balance.spending_limit_per_session ?? 0}</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <ShieldAlert size={17} className="mt-0.5 shrink-0 text-[color:var(--gold)]" />
          <div>
            <p className="text-sm text-[color:var(--text-muted)]">Low alert limit</p>
            <p className="title-small text-[color:var(--text)]">{balance.low_balance_threshold ?? 0}</p>
          </div>
        </div>
      </div>
    </motion.article>
  );
}
