"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import type { WalletBalance, WalletTransaction, WalletUsage } from "@/lib/api";
import { getTransactions, getUsage, getWalletBalance, topUpWallet } from "@/lib/api";
import { WalletCard } from "@/components/WalletCard";

export default function WalletPage() {
  const [balance, setBalance] = useState<WalletBalance | null>(null);
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [usage, setUsage] = useState<WalletUsage | null>(null);
  const [amount, setAmount] = useState("500");
  const [pending, setPending] = useState(false);
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

  async function handleTopup(event: FormEvent) {
    event.preventDefault();
    const credits = Number(amount);
    if (!Number.isFinite(credits) || credits <= 0) {
      setError("Please enter a positive top-up amount.");
      return;
    }

    try {
      setPending(true);
      const next = await topUpWallet(credits);
      setBalance(next);
      setError(null);
    } catch {
      setError("Top-up failed. Please retry.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold text-white">Wallet</h1>
        <p className="mt-2 text-sm text-[color:var(--text-muted)]">
          Track credits, top up quickly, and review usage by tool.
        </p>
      </header>

      {balance ? <WalletCard balance={balance} /> : null}
      {error ? <p className="text-sm text-amber-200">{error}</p> : null}

      <form onSubmit={handleTopup} className="rounded-xl border border-white/10 bg-[color:var(--surface)] p-4">
        <label className="block text-sm text-[color:var(--text-muted)]">
          Add Credits
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <input
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
              inputMode="numeric"
              className="w-40 rounded-lg border border-white/15 bg-slate-900/80 px-3 py-2 text-sm text-white"
            />
            <button
              disabled={pending}
              className="rounded-lg bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-cyan-200 disabled:opacity-60"
            >
              {pending ? "Processing..." : "Add Credits"}
            </button>
          </div>
        </label>
      </form>

      <section className="rounded-xl border border-white/10 bg-[color:var(--surface)] p-4">
        <h2 className="text-lg font-semibold text-white">Recent Transactions</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.12em] text-[color:var(--text-muted)]">
              <tr>
                <th className="py-2">Time</th>
                <th className="py-2">Type</th>
                <th className="py-2">Amount</th>
                <th className="py-2">Tool</th>
                <th className="py-2">Balance After</th>
              </tr>
            </thead>
            <tbody>
              {transactions.slice(0, 12).map((txn) => (
                <tr key={txn.id} className="border-t border-white/10">
                  <td className="py-2 text-[color:var(--text-muted)]">
                    {txn.created_at ? new Date(txn.created_at).toLocaleString() : "-"}
                  </td>
                  <td className="py-2 text-white">{txn.type}</td>
                  <td className="py-2 text-white">{txn.amount}</td>
                  <td className="py-2 text-[color:var(--text-muted)]">{txn.tool_name ?? "-"}</td>
                  <td className="py-2 text-[color:var(--text-muted)]">{txn.balance_after}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-white/10 bg-[color:var(--surface)] p-4">
        <h2 className="text-lg font-semibold text-white">Usage by Tool</h2>
        <div className="mt-3 space-y-2">
          {usageRows.map(([toolName, info]) => (
            <article key={toolName} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2 text-sm">
              <p className="text-white">{toolName}</p>
              <p className="text-[color:var(--text-muted)]">
                {info.calls} calls • {info.total_credits} credits • {info.errors} errors
              </p>
            </article>
          ))}
          {!usageRows.length ? <p className="text-sm text-[color:var(--text-muted)]">No usage data yet.</p> : null}
        </div>
      </section>
    </section>
  );
}
