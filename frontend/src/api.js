const BASE_URL = import.meta.env.VITE_API_URL || "https://ai-codebase-intlligence.onrender.com";

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
