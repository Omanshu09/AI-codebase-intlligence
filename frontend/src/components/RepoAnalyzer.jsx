import { useState, useEffect } from "react";
import { api } from "../api";

export default function RepoAnalyzer({ repositories, onRepositoriesChange, selectedId, onSelect }) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const refresh = async () => {
    const repos = await api.listRepositories();
    onRepositoriesChange(repos);
  };

  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError("");
    try {
      const repo = await api.ingestRepository(url.trim());
      setUrl("");
      await refresh();
      onSelect(repo.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    await api.deleteRepository(id);
    if (selectedId === id) onSelect(null);
    refresh();
  };

  return (
    <div className="panel">
      <h1>AI Codebase Intelligence</h1>
      <p className="subtitle">Paste a public GitHub repo URL to index it, then ask questions below.</p>

      <form className="row" onSubmit={handleAnalyze}>
        <input
          placeholder="https://github.com/user/project"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Analyzing…" : "Analyze Repository"}
        </button>
      </form>
      {error && <div className="error">{error}</div>}

      <div className="repo-list">
        {repositories.length === 0 && <div className="muted">No repositories indexed yet.</div>}
        {repositories.map((repo) => (
          <div
            key={repo.id}
            className={`repo-item ${selectedId === repo.id ? "active" : ""}`}
            onClick={() => onSelect(repo.id)}
          >
            <div>
              <strong>{repo.name}</strong>{" "}
              <span className="muted">
                {repo.file_count} files · {repo.chunk_count} chunks
              </span>
            </div>
            <div className="row" style={{ alignItems: "center" }}>
              <span className={`badge ${repo.status}`}>{repo.status}</span>
              <button onClick={(e) => handleDelete(repo.id, e)} style={{ background: "#2a2e37" }}>
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
