// Checked in this order: runtime config.js (editable post-build, see
// public/config.js) -> Vite build-time env var -> localhost fallback for
// local dev only. This was previously build-time-only, which is why the
// deployed Vercel site was silently calling localhost and failing.
const BASE_URL = window.__API_BASE_URL__ || import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  listRepositories: () => request("/repositories"),
  ingestRepository: (repo_url) =>
    request("/repositories/ingest", {
      method: "POST",
      body: JSON.stringify({ repo_url }),
    }),
  deleteRepository: (id) =>
    request(`/repositories/${id}`, { method: "DELETE" }),
  askQuestion: (repository_id, question) =>
    request("/query", {
      method: "POST",
      body: JSON.stringify({ repository_id, question }),
    }),
};
