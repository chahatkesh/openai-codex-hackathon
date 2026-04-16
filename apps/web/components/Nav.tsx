"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Box, Menu, X } from "lucide-react";
import { useState } from "react";

const LINKS = [
  { href: "/catalog", label: "Catalog" },
  { href: "/wallet", label: "Wallet" },
  { href: "/feed", label: "Live Feed" },
  { href: "/integrate", label: "Integrate" },
  { href: "/connect", label: "Connect" },
];

export function Nav() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b table-rule bg-[color:var(--background)]/88 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1200px] items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="group flex min-w-0 items-center gap-3">
          <motion.span
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.98 }}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[8px] border table-rule bg-[color:var(--surface-strong)] text-[color:var(--text)]"
            aria-hidden="true"
          >
            <Box size={18} strokeWidth={1.8} />
          </motion.span>
          <span className="min-w-0 leading-tight">
            <span className="block truncate text-sm font-medium text-[color:var(--text)] transition-colors group-hover:text-[color:var(--accent)]">
              FuseKit
            </span>
            <span className="block truncate text-xs text-[color:var(--text-muted)]">Agent tool marketplace</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Primary navigation">
          {LINKS.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative rounded-[8px] px-3 py-2 text-sm transition-colors ${
                  active ? "text-[color:var(--text)]" : "text-[color:var(--text-muted)] hover:text-[color:var(--text)]"
                }`}
              >
                {active ? (
                  <motion.span
                    layoutId="nav-indicator"
                    className="absolute inset-0 rounded-[8px] bg-[color:var(--surface)]"
                    initial={false}
                    transition={{ type: "spring", bounce: 0.22, duration: 0.42 }}
                  />
                ) : null}
                <span className="relative z-10">{link.label}</span>
              </Link>
            );
          })}
        </nav>

        <Link href="/integrate" className="button-warm hidden md:inline-flex">
          Request tool
        </Link>

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
        className="overflow-hidden border-t table-rule bg-[color:var(--background-soft)] md:hidden"
        aria-label="Mobile navigation"
      >
        <div className="space-y-1 px-4 py-3">
          {LINKS.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`block rounded-[8px] px-3 py-2 text-sm ${
                  active ? "bg-[color:var(--surface)] text-[color:var(--text)]" : "text-[color:var(--text-muted)]"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </motion.nav>
    </header>
  );
}
