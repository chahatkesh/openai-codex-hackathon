"use client";

import { useEffect, useMemo, useState } from "react";
import type { WalletBalance, WalletTransaction, WalletUsage } from "@/lib/api";
import { getTransactions, getUsage, getWalletBalance } from "@/lib/api";
import { WalletCard } from "@/components/WalletCard";

export default function WalletPage() {
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [usage, setUsage] = useState<WalletUsage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [nextBalance, nextTransactions, nextUsage] = await Promise.all([
          getWalletBalance(),
          getTransactions(),
          getUsage(),
        ]);
        setBalance(nextBalance);
        setTransactions(nextTransactions);
        setUsage(nextUsage);
        setError(null);
      } catch {
        setError("Wallet endpoints unavailable. Retrying automatically.");
      }
    };

    load();
    const timer = window.setInterval(load, 5000);
    return () => window.clearInterval(timer);
  }, []);

  const usageRows = useMemo(() => {
    if (!usage) return [];
    return Object.entries(usage.by_tool).sort((a, b) => b[1].calls - a[1].calls);
  }, [usage]);

  return (
    <section className="space-y-6 pb-12">
      <header className="surface-card-light p-6">
        <p className="eyebrow">Credits and enforcement</p>
        <h1 className="section-title mt-3 text-[color:var(--text)]">Wallet</h1>
        <p className="body-serif mt-2 max-w-2xl">Track balance and inspect usage before demo calls drain credits.</p>
      </header>

      {balance ? <WalletCard balance={balance} /> : null}
      {error ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{error}</p> : null}

      <section className="surface-card-light p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="eyebrow">Ledger</p>
            <h2 className="title-small mt-1 text-[color:var(--text)]">Recent transactions</h2>
          </div>
          <span className="pill">{transactions.length} rows</span>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b table-rule text-xs text-[color:var(--text-muted)]">
              <tr>
                <th className="py-3 font-medium">Time</th>
                <th className="py-3 font-medium">Type</th>
                <th className="py-3 font-medium">Amount</th>
                <th className="py-3 font-medium">Tool</th>
                <th className="py-3 font-medium">Balance after</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[rgba(38,37,30,0.1)]">
              {transactions.slice(0, 12).map((txn) => (
                <tr key={txn.id}>
                  <td className="py-3 text-[color:var(--text-muted)]">{txn.created_at ? new Date(txn.created_at).toLocaleString() : "-"}</td>
                  <td className="py-3 text-[color:var(--text)]">{txn.type}</td>
                  <td className="py-3 mono-text text-xs text-[color:var(--accent)]">{txn.amount}</td>
                  <td className="py-3 text-[color:var(--text-muted)]">{txn.tool_name ?? "-"}</td>
                  <td className="py-3 text-[color:var(--text-muted)]">{txn.balance_after}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!transactions.length ? <p className="mt-4 text-sm text-[color:var(--text-muted)]">No transactions yet.</p> : null}
        </div>
      </section>

      <section className="surface-card p-5">
        <p className="eyebrow">Tool usage</p>
        <h2 className="title-small mt-1 text-[color:var(--text)]">Usage by tool</h2>
        <div className="mt-4 divide-y divide-[rgba(38,37,30,0.1)]">
          {usageRows.map(([toolName, info]) => (
            <article key={toolName} className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
              <p className="mono-text break-words text-xs text-[color:var(--text)]">{toolName}</p>
              <p className="text-[color:var(--text-muted)]">
                {info.calls} calls / {info.total_credits} credits / {info.errors} errors
              </p>
            </article>
          ))}
          {!usageRows.length ? <p className="py-3 text-sm text-[color:var(--text-muted)]">No usage data yet.</p> : null}
        </div>
      </section>
    </section>
  );
}
