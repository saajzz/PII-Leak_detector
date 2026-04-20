const API_BASE = "http://localhost:5000/api";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export async function postJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST" });
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  getStats: () => fetchJSON<Record<string, number>>("/stats"),
  getIncidents: () => fetchJSON<any[]>("/incidents"),
  getFindings: () => fetchJSON<any[]>("/findings"),
  getSeverityBreakdown: () => fetchJSON<Record<string, number>>("/severity-breakdown"),
  getSources: () => fetchJSON<Record<string, number>>("/sources"),
  getCanaries: () => fetchJSON<any[]>("/canaries"),
  runPipeline: () => postJSON<any>("/run-pipeline"),
};
