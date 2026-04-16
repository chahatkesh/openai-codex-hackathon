"use client";

import type { WalletBalance } from "@/lib/api";
import { motion } from "framer-motion";
import { Wallet, ShieldAlert, BadgeInfo } from "lucide-react";

type Props = {
  balance: WalletBalance;
};

export function WalletCard({ balance }: Props) {
  return (
    <motion.article 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", bounce: 0.4 }}
      className="relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br from-[color:var(--surface)] to-[color:var(--background-soft)] p-8 shadow-2xl shadow-teal-500/5 group"
    >
      <div className="absolute right-0 top-0 h-48 w-48 -translate-y-12 translate-x-12 rounded-full bg-teal-500/10 blur-[80px] transition-all group-hover:bg-teal-500/20"></div>

      <div className="relative z-10 flex items-center justify-between mb-8">
        <div className="flex items-center gap-3 bg-teal-500/10 text-teal-400 p-3 rounded-2xl border border-teal-500/20">
          <Wallet size={24} />
        </div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 border border-white/5 rounded-full px-4 py-1.5 backdrop-blur-sm bg-white/5">
          Available Balance
        </p>
      </div>

      <div className="relative z-10 mt-2 mb-10 flex items-baseline gap-2">
        <motion.p 
          key={balance.balance}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-teal-200 to-cyan-400 drop-shadow-sm"
        >
          {balance.balance.toLocaleString()}
        </motion.p>
        <span className="text-lg font-medium text-slate-400">credits</span>
      </div>

      <div className="relative z-10 grid gap-3 text-sm text-slate-400 sm:grid-cols-2">
        <div className="flex flex-col gap-1.5 p-4 rounded-xl bg-white/[0.03] border border-white/5">
          <div className="flex items-center gap-2 text-teal-300">
            <BadgeInfo size={16} /> 
            <span className="text-xs font-bold uppercase tracking-wider">Session Limit</span>
          </div>
          <p className="text-xl font-bold text-white pl-6">{balance.spending_limit_per_session ?? 0}</p>
        </div>
        <div className="flex flex-col gap-1.5 p-4 rounded-xl bg-white/[0.03] border border-white/5">
          <div className="flex items-center gap-2 text-amber-300">
            <ShieldAlert size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Low Alert Limit</span>
          </div>
          <p className="text-xl font-bold text-white pl-6">{balance.low_balance_threshold ?? 0}</p>
        </div>
      </div>
    </motion.article>
  );
}
