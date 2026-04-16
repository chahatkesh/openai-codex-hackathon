"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Fingerprint, Link as LinkIcon, PlugZap } from "lucide-react";

type Props = {
  onSubmit: (payload: { docsUrl: string; toolName?: string }) => Promise<void>;
  disabled?: boolean;
};

export function DocsUrlForm({ onSubmit, disabled }: Props) {
  const [docsUrl, setDocsUrl] = useState("");
  const [toolName, setToolName] = useState("");

  return (
    <motion.form
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      onSubmit={async (event) => {
        event.preventDefault();
        await onSubmit({ docsUrl, toolName: toolName || undefined });
      }}
      className="surface-card-light elevated-card space-y-5 p-6"
    >
      <div>
        <label htmlFor="docsUrl" className="mb-2 flex items-center gap-2 text-sm text-[color:var(--text)]">
          <LinkIcon size={15} className="text-[color:var(--accent)]" />
          API documentation URL
        </label>
        <input
          id="docsUrl"
          type="url"
          required
          value={docsUrl}
          onChange={(event) => setDocsUrl(event.target.value)}
          placeholder="https://developer.example.com/docs"
          className="input-warm"
        />
      </div>

      <div>
        <label htmlFor="toolName" className="mb-2 flex items-center gap-2 text-sm text-[color:var(--text)]">
          <Fingerprint size={15} className="text-[color:var(--accent)]" />
          Suggested tool name <span className="text-[color:var(--text-muted)]">(optional)</span>
        </label>
        <input
          id="toolName"
          type="text"
          value={toolName}
          onChange={(event) => setToolName(event.target.value)}
          placeholder="send_slack_message"
          className="input-warm mono-text"
        />
      </div>

      <motion.button
        type="submit"
        disabled={disabled}
        whileHover={!disabled ? { y: -1 } : {}}
        whileTap={!disabled ? { scale: 0.99 } : {}}
        className={`button-warm button-accent w-full ${disabled ? "cursor-not-allowed opacity-55" : ""}`}
      >
        <PlugZap size={17} />
        {disabled ? "Queueing integration..." : "Trigger auto-integration"}
      </motion.button>
    </motion.form>
  );
}
