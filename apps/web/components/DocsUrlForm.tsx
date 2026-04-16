"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { PlugZap, Link as LinkIcon, Fingerprint } from "lucide-react";

type Props = {
  onSubmit: (payload: { docsUrl: string; toolName?: string }) => Promise<void>;
  disabled?: boolean;
};

export function DocsUrlForm({ onSubmit, disabled }: Props) {
  const [docsUrl, setDocsUrl] = useState("");
  const [toolName, setToolName] = useState("");
  const [isHovered, setIsHovered] = useState(false);

  return (
    <motion.form
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      onSubmit={async (event) => {
        event.preventDefault();
        await onSubmit({ docsUrl, toolName: toolName || undefined });
      }}
      className="relative space-y-6 rounded-2xl border border-white/5 bg-gradient-to-br from-[color:var(--surface)] to-[color:var(--background-soft)] p-8 shadow-xl shadow-teal-500/5 group"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className={`absolute -inset-px transition-opacity duration-500 rounded-2xl bg-gradient-to-r from-teal-500/20 via-cyan-500/10 to-transparent blur opacity-0 ${isHovered ? 'opacity-100' : ''}`} />

      <div className="relative z-10">
        <label htmlFor="docsUrl" className="mb-2 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-300">
          <LinkIcon size={16} className="text-teal-400" /> API Documentation URL
        </label>
        <div className="relative">
          <input
            id="docsUrl"
            type="url"
            required
            value={docsUrl}
            onChange={(event) => setDocsUrl(event.target.value)}
            placeholder="https://developer.example.com/docs"
            className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 pl-11 text-sm text-white outline-none ring-teal-400/30 placeholder:text-slate-600 focus:border-teal-400/50 focus:ring-2 transition-all shadow-inner backdrop-blur-md"
          />
          <div className="absolute left-4 top-1/2 -translate-y-1/2 opacity-40">
            <LinkIcon size={16} />
          </div>
        </div>
      </div>

      <div className="relative z-10">
        <label htmlFor="toolName" className="mb-2 flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-300">
          <Fingerprint size={16} className="text-cyan-400" /> Suggested Tool Name <span className="text-slate-500 font-medium">(Optional)</span>
        </label>
        <div className="relative">
          <input
            id="toolName"
            type="text"
            value={toolName}
            onChange={(event) => setToolName(event.target.value)}
            placeholder="send_slack_message"
            className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 pl-11 text-sm text-white outline-none ring-cyan-400/30 placeholder:text-slate-600 focus:border-cyan-400/50 focus:ring-2 transition-all shadow-inner backdrop-blur-md"
          />
          <div className="absolute left-4 top-1/2 -translate-y-1/2 opacity-40">
            <PlugZap size={16} />
          </div>
        </div>
      </div>

      <motion.button
        type="submit"
        disabled={disabled}
        whileHover={!disabled ? { scale: 1.02 } : {}}
        whileTap={!disabled ? { scale: 0.98 } : {}}
        className={`relative w-full z-10 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-teal-400 to-cyan-500 px-5 py-3.5 text-sm font-bold shadow-lg shadow-teal-500/25 transition-all outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2 focus:ring-offset-[color:var(--background)] ${
          disabled 
            ? "cursor-not-allowed opacity-50 grayscale saturate-50" 
            : "hover:shadow-teal-500/40 text-slate-900"
        }`}
      >
        <PlugZap size={18} className={disabled ? "" : "animate-pulse"} />
        Trigger Auto-Integration
      </motion.button>
    </motion.form>
  );
}
