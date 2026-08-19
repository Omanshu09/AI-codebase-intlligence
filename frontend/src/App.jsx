import { useState, useMemo } from "react";
import RepoAnalyzer from "./components/RepoAnalyzer.jsx";
import ChatInterface from "./components/ChatInterface.jsx";

export default function App() {
  const [repositories, setRepositories] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  const selected = useMemo(
    () => repositories.find((r) => r.id === selectedId),
    [repositories, selectedId]
  );

  return (
    <div className="app">
      <RepoAnalyzer
        repositories={repositories}
        onRepositoriesChange={setRepositories}
        selectedId={selectedId}
        onSelect={setSelectedId}
      />
      <ChatInterface
        repositoryId={selected && selected.status === "ready" ? selected.id : null}
        repositoryName={selected?.name}
      />
    </div>
  );
}
