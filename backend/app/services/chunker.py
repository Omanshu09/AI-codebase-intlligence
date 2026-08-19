from dataclasses import dataclass, field
from typing import List, Optional

from app.services.parser import parse_file, Symbol

MAX_CHUNK_LINES = 120  # hard cap so no single chunk is absurdly large
MIN_STANDALONE_LINES = 3  # skip trivial one-liners as their own chunk


@dataclass
class CodeChunk:
    file_path: str
    language: str
    content: str
    symbol: Optional[str]
    kind: str
    start_line: int
    end_line: int


LANGUAGE_BY_EXT = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
}


def _language_for(path: str) -> str:
    for ext, lang in LANGUAGE_BY_EXT.items():
        if path.endswith(ext):
            return lang
    return "text"


def chunk_file(path: str, source: str) -> List[CodeChunk]:
    """
    Splits one file's source into CodeChunks aligned to function/class
    boundaries where possible. Falls back to fixed-size line windows for
    files with no recognizable symbols (config files, plain scripts, etc).
    """
    lines = source.splitlines()
    if not lines:
        return []

    language = _language_for(path)
    symbols: List[Symbol] = parse_file(path, source)
    chunks: List[CodeChunk] = []

    if symbols:
        for sym in symbols:
            start = max(sym.start_line - 1, 0)
            end = min(sym.end_line, len(lines))
            if end - start < MIN_STANDALONE_LINES:
                continue
            # cap very long symbols
            end = min(end, start + MAX_CHUNK_LINES)
            content = "\n".join(lines[start:end]).strip()
            if not content:
                continue
            chunks.append(CodeChunk(
                file_path=path, language=language, content=content,
                symbol=sym.name, kind=sym.kind,
                start_line=start + 1, end_line=end,
            ))
    else:
        # No symbols found (e.g. config/markup files) -> fixed-size windows
        for start in range(0, len(lines), MAX_CHUNK_LINES):
            end = min(start + MAX_CHUNK_LINES, len(lines))
            content = "\n".join(lines[start:end]).strip()
            if content:
                chunks.append(CodeChunk(
                    file_path=path, language=language, content=content,
                    symbol=None, kind="block",
                    start_line=start + 1, end_line=end,
                ))

    return chunks
