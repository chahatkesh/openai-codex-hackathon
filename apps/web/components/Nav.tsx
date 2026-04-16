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
    <header className="sticky top-0 z-30 border-b border-white/5 bg-[color:var(--background)]/80 backdrop-blur-xl shadow-sm transition-all">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="group flex items-center gap-3">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-400 text-slate-900 font-black shadow-lg shadow-teal-500/20"
          >
            <Box size={20} />
          </motion.div>
          <div className="leading-tight">
            <p className="text-sm font-bold tracking-[0.2em] text-teal-300 group-hover:text-teal-200 transition-colors">
              FUSEKIT
            </p>
            <p className="text-xs text-[color:var(--text-muted)] font-medium">Agentic API Hub</p>
          </div>
        </Link>

        {/* Desktop Menu */}
        <nav className="hidden items-center gap-2 md:flex">
          {LINKS.map((link) => {
            const active = pathname === link.href || (link.href !== '/' && pathname.startsWith(`${link.href}/`));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative px-4 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "text-teal-300"
                    : "text-[color:var(--text-muted)] hover:text-white"
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="nav-indicator"
                    className="absolute inset-0 rounded-lg bg-teal-500/10"
                    initial={false}
                    transition={{ type: "spring", bounce: 0.25, duration: 0.5 }}
                  />
                )}
                <span className="relative z-10">{link.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Mobile Menu Toggle */}
        <button 
          className="md:hidden p-2 text-slate-400 hover:text-white"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Nav */}
      <motion.div 
        initial={false}
        animate={{ height: mobileMenuOpen ? "auto" : 0, opacity: mobileMenuOpen ? 1 : 0 }}
        className="md:hidden overflow-hidden bg-[color:var(--surface)] border-b border-white/5"
      >
        <div className="px-4 py-3 space-y-1">
          {LINKS.map((link) => {
            const active = pathname === link.href || (link.href !== '/' && pathname.startsWith(`${link.href}/`));
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`block rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                  active
                    ? "bg-teal-500/15 text-teal-300"
                    : "text-[color:var(--text-muted)] hover:bg-white/5 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </motion.div>
    </header>
  );
}
