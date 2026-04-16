const JOB_IDS_KEY = "fusekit.integrationJobIds";

export function addTrackedJobId(jobId: string) {
  if (typeof window === "undefined") return;
  const all = getTrackedJobIds();
  if (!all.includes(jobId)) {
    const next = [jobId, ...all].slice(0, 20);
    window.localStorage.setItem(JOB_IDS_KEY, JSON.stringify(next));
  }
}

export function getTrackedJobIds(): string[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(JOB_IDS_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed)
      ? parsed.filter((id): id is string => typeof id === "string")
      : [];
  } catch {
    return [];
  }
}
