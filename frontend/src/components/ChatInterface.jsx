import { useState } from "react";
import { api } from "../api";

export default function ChatInterface({ repositoryId, repositoryName }) {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim() || !repositoryId) return;
    const q = question.trim();
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setQuestion("");
    setLoading(true);
    setError("");
    try {
      const res = await api.askQuestion(repositoryId, q);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer, sources: res.sources }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!repositoryId) {
    return (
      <div className="panel">
        <p className="muted">Select a ready repository above to start asking questions about its code.</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h2 style={{ marginTop: 0, fontSize: 16 }}>Ask about {repositoryName}</h2>

      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.content}
            {m.sources && m.sources.length > 0 && (
              <div className="sources">
                <div>Sources:</div>
                {m.sources.map((s, j) => (
                  <div className="source-item" key={j}>
                    <code>{s.file_path}</code>
                    {s.symbol && <> — {s.symbol}</>}
                    {s.start_line && <> (lines {s.start_line}-{s.end_line})</>}
                    {" · "}score {s.score}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <form className="row" onSubmit={handleAsk}>
        <input
          placeholder="Where is authentication implemented?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
