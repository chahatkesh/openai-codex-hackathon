"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { getProviderCredentials, saveProviderCredentials, type ProviderCredentialStatus } from "@/lib/api";

export default function CredentialsPage() {
  const [providers, setProviders] = useState<ProviderCredentialStatus[]>([]);
  const [drafts, setDrafts] = useState<Record<string, Record<string, string>>>({});
  const [savingProvider, setSavingProvider] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const next = await getProviderCredentials();
        setProviders(next.filter((provider) => provider.requirements.length > 0));
        setError(null);
      } catch {
        setError("Credential endpoints unavailable. Retry after the platform restarts.");
      }
    };

    load();
    const timer = window.setInterval(load, 5000);
    return () => window.clearInterval(timer);
  }, []);

  async function handleSubmit(event: FormEvent, provider: ProviderCredentialStatus) {
    event.preventDefault();
    const values = drafts[provider.provider] ?? {};
    setSavingProvider(provider.provider);
    try {
      const updated = await saveProviderCredentials(provider.provider, values);
      setProviders((current) =>
        current.map((item) => (item.provider === updated.provider ? updated : item)),
      );
      setDrafts((current) => ({ ...current, [provider.provider]: {} }));
      setError(null);
    } catch {
      setError(`Could not save credentials for ${provider.display_name}.`);
    } finally {
      setSavingProvider(null);
    }
  }

  return (
    <section className="space-y-6 pb-12">
      <header className="surface-card-light p-6">
        <p className="eyebrow">Admin credentials</p>
        <h1 className="section-title mt-3 text-[color:var(--text)]">Provider credentials</h1>
        <p className="body-serif mt-2 max-w-3xl">
          Pending tools land here when they need provider secrets. Add the required values to activate the provider and
          let those tools move from pending credentials to live execution.
        </p>
        <p className="mt-3 text-sm text-[color:var(--text-muted)]">
          After saving credentials, return to the{" "}
          <Link href="/catalog" className="warm-link underline">
            catalog
          </Link>{" "}
          or{" "}
          <Link href="/feed" className="warm-link underline">
            live feed
          </Link>{" "}
          to confirm the updated state.
        </p>
      </header>

      {error ? <p className="surface-card-light p-3 text-sm text-[color:var(--gold)]">{error}</p> : null}

      <div className="grid gap-4">
        {providers.map((provider) => (
          <article key={provider.provider} className="surface-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="eyebrow">{provider.provider}</p>
                <h2 className="title-small mt-2 text-[color:var(--text)]">{provider.display_name}</h2>
                <p className="mt-2 text-sm text-[color:var(--text-muted)]">
                  {provider.is_configured
                    ? "All required credentials are configured."
                    : "Add the required credentials below to activate pending tools."}
                </p>
              </div>
              <span className="pill">{provider.is_configured ? "configured" : "needs setup"}</span>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {(provider.affected_tools ?? []).map((tool) => (
                <span key={tool.name} className="pill">
                  {tool.name} · {tool.status}
                </span>
              ))}
            </div>

            <form onSubmit={(event) => handleSubmit(event, provider)} className="mt-5 grid gap-4 md:grid-cols-2">
              {provider.requirements.map((requirement) => (
                <label key={requirement.key} className="text-sm text-[color:var(--text-muted)]">
                  {requirement.label}
                  <input
                    type="password"
                    value={drafts[provider.provider]?.[requirement.key] ?? ""}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [provider.provider]: {
                          ...(current[provider.provider] ?? {}),
                          [requirement.key]: event.target.value,
                        },
                      }))
                    }
                    placeholder={provider.configured_keys.includes(requirement.key) ? "Already configured" : requirement.key}
                    className="input-warm mt-2"
                  />
                </label>
              ))}

              <div className="md:col-span-2 flex flex-wrap items-center gap-3">
                <button
                  type="submit"
                  disabled={savingProvider === provider.provider}
                  className={`button-warm button-accent ${savingProvider === provider.provider ? "cursor-not-allowed opacity-55" : ""}`}
                >
                  {savingProvider === provider.provider ? "Saving..." : "Save credentials"}
                </button>
                <span className="text-xs text-[color:var(--text-muted)]">
                  Configured keys: {provider.configured_keys.length ? provider.configured_keys.join(", ") : "none"}
                </span>
              </div>
            </form>
          </article>
        ))}
      </div>

      {!providers.length && !error ? (
        <p className="surface-card-light p-4 text-sm text-[color:var(--text-muted)]">
          No credential-managed providers are currently visible.
        </p>
      ) : null}
    </section>
  );
}
