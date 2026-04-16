"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Box, Menu, Radio, X } from "lucide-react";
import { useState } from "react";

const LINKS = [
  { href: "/catalog", label: "Catalog" },
  { href: "/wallet", label: "Wallet" },
  { href: "/feed", label: "Live feed" },
  { href: "/connect", label: "Connect Codex" },
];

export function Nav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 px-3 py-3 backdrop-blur-xl sm:px-4">
      <div className="nav-shell mx-auto flex w-full max-w-[1200px] items-center justify-between gap-3 px-3 py-2 sm:px-4">
        <Link href="/" className="group flex min-w-0 items-center gap-3">
          <motion.span
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.98 }}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[8px] bg-[color:var(--text)] text-[color:var(--surface-light)]"
            aria-hidden="true"
          >
            <Box size={18} strokeWidth={1.8} />
          </motion.span>
          <span className="min-w-0 leading-tight">
            <span className="block truncate text-sm font-medium text-[color:var(--text)] transition-colors group-hover:text-[color:var(--accent)]">
              FuseKit
            </span>
            <span className="hidden truncate text-xs text-[color:var(--text-muted)] sm:block">Agentic API marketplace</span>
          </span>
        </Link>

        <nav
          className="hidden items-center gap-1 rounded-[8px] border table-rule bg-[color:var(--background)] p-1 md:flex"
          aria-label="Primary navigation"
        >
          {LINKS.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                className={`relative rounded-[7px] px-3 py-2 text-sm transition-colors ${
                  active ? "text-[color:var(--text)]" : "text-[color:var(--text-muted)] hover:text-[color:var(--text)]"
                }`}
              >
                {active ? (
                  <motion.span
                    layoutId="nav-indicator"
                    className="absolute inset-0 rounded-[7px] bg-[color:var(--surface-strong)] shadow-[rgba(0,0,0,0.04)_0_4px_12px]"
                    initial={false}
                    transition={{ type: "spring", bounce: 0.2, duration: 0.42 }}
                  />
                ) : null}
                <span className="relative z-10">{link.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <span className="pill bg-[rgba(31,138,101,0.1)] text-[color:var(--success)]">
            <Radio size={12} />
            Live MCP
          </span>
          <Link href="/integrate" className="button-warm button-accent">
            Request tool
          </Link>
        </div>

        <button
          type="button"
          className="button-warm md:hidden"
          onClick={() => setMobileMenuOpen((open) => !open)}
          aria-label={mobileMenuOpen ? "Close navigation" : "Open navigation"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      <motion.nav
        initial={false}
        animate={{ height: mobileMenuOpen ? "auto" : 0, opacity: mobileMenuOpen ? 1 : 0 }}
        className="mx-auto mt-2 max-w-[1200px] overflow-hidden rounded-[8px] border table-rule bg-[color:var(--surface-light)] md:hidden"
        aria-label="Mobile navigation"
      >
        <div className="space-y-1 p-2">
          {LINKS.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
                onClick={() => setMobileMenuOpen(false)}
                className={`block rounded-[8px] px-3 py-2 text-sm ${
                  active ? "bg-[color:var(--surface-strong)] text-[color:var(--text)]" : "text-[color:var(--text-muted)]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <Link href="/integrate" onClick={() => setMobileMenuOpen(false)} className="button-warm button-accent mt-2 w-full">
            Request tool
          </Link>
        </div>
      </motion.nav>
    </header>
  );
}
