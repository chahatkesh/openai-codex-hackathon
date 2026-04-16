export type ToolStatus = "live" | "pending_credentials" | "deprecated" | "integrating" | "failed";

export type CatalogItem = {
  id: string;
  name: string;
  description: string;
  provider: string;
  cost_per_call: number;
  status: ToolStatus;
  category?: string;
  input_schema?: Record<string, unknown>;
  source?: string;
  version?: number;
  created_at?: string;
};

export type CatalogStats = {
  total: number;
  live: number;
  pending_credentials: number;
  by_category: Record<string, number>;
};

export type WalletBalance = {
  balance: number;
  spending_limit_per_session?: number;
  low_balance_threshold?: number;
};

export type WalletTransaction = {
  id: string;
  type: "debit" | "credit";
  amount: number;
  tool_name?: string | null;
  reference?: string | null;
  balance_after: number;
  created_at?: string;
};

export type WalletUsage = {
  total_calls: number;
  by_tool: Record<string, { calls: number; total_credits: number; errors: number }>;
};

export type IntegrationRequest = {
  docs_url: string;
  requested_by?: "user" | "mcp_tool_miss" | "crawler";
  requested_tool_name?: string;
};

export type IntegrationJobStatus = {
  job_id?: string;
  id?: string;
  status: "queued" | "running" | "complete" | "failed" | string;
  current_stage?: string | null;
  error_log?: string | null;
  resulting_tool_id?: string | null;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class EndpointUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EndpointUnavailableError";
  }
}

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

function toUrl(path: string): string {
  return path.startsWith("http") ? path : `${API_BASE_URL}${path}`;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(toUrl(path), {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new EndpointUnavailableError(`Could not reach ${path}`);
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    if (response.status === 404 || response.status >= 500) {
      throw new EndpointUnavailableError(`${path} is currently unavailable (${response.status})`);
    }
    throw new ApiError(`Request failed for ${path}`, response.status, payload);
  }

  return payload as T;
}

export async function getCatalog(filters?: { status?: string; category?: string }) {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.category) params.set("category", filters.category);
  const query = params.toString();
  return fetchJson<CatalogItem[]>(`/api/catalog${query ? `?${query}` : ""}`);
}

export async function getRecentTools() {
  return fetchJson<CatalogItem[]>("/api/catalog/recent");
}

export async function getCatalogStats() {
  return fetchJson<CatalogStats>("/api/catalog/stats");
}

export async function getWalletBalance() {
  return fetchJson<WalletBalance>("/api/wallet/balance");
}

export async function topUpWallet(amount: number) {
  return fetchJson<WalletBalance>("/api/wallet/topup", {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export async function getTransactions() {
  return fetchJson<WalletTransaction[]>("/api/wallet/transactions");
}

export async function getUsage() {
  return fetchJson<WalletUsage>("/api/wallet/usage");
}

export async function triggerIntegration(docsUrl: string, toolName?: string) {
  return fetchJson<IntegrationJobStatus>("/api/integrate", {
    method: "POST",
    body: JSON.stringify({
      docs_url: docsUrl,
      requested_by: "user",
      requested_tool_name: toolName || undefined,
    } satisfies IntegrationRequest),
  });
}

export async function getJobStatus(jobId: string) {
  return fetchJson<IntegrationJobStatus>(`/api/integrate/${jobId}`);
}

export async function getRecentJobs(limit = 20) {
  return fetchJson<IntegrationJobStatus[]>(`/api/integrate?limit=${limit}`);
}

export const apiBaseUrl = API_BASE_URL;
