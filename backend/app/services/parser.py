"""
Turns a source file's raw text into a list of "symbols" (functions, classes,
methods) with their line ranges, so the chunker can split code along
meaningful boundaries instead of arbitrary character counts.

Python files are parsed with the built-in `ast` module for accuracy.
Every other supported language falls back to a lightweight regex scan
that recognizes common function/class declaration patterns. This is not
as precise as a real parser, but it's dependency-free and works well
enough for chunk boundaries. Swapping this module for `tree-sitter` is
the natural next upgrade if you want multi-language AST-level accuracy.
"""
import ast
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Symbol:
    name: str
    kind: str  # "function" | "class" | "method"
    start_line: int
    end_line: int


def parse_python(source: str) -> List[Symbol]:
    symbols: List[Symbol] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return symbols

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            symbols.append(Symbol(node.name, "function", node.lineno, end))
        elif isinstance(node, ast.ClassDef):
            end = getattr(node, "end_lineno", node.lineno)
            symbols.append(Symbol(node.name, "class", node.lineno, end))

    return symbols


_GENERIC_PATTERNS = [
    # JS/TS function declarations & arrow functions assigned to a const
    re.compile(r'^\s*(export\s+)?(async\s+)?function\s+([A-Za-z0-9_]+)\s*\('),
    re.compile(r'^\s*(export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(async\s*)?\('),
    # Classes (JS/TS/Java/C#/PHP/etc)
    re.compile(r'^\s*(export\s+)?(public\s+|private\s+)?class\s+([A-Za-z0-9_]+)'),
    # Go functions
    re.compile(r'^\s*func\s+(\([^)]*\)\s*)?([A-Za-z0-9_]+)\s*\('),
    # Java/C#/C++ methods (rough heuristic: return type + name + paren + brace)
    re.compile(r'^\s*(public|private|protected|static)\s+[\w<>\[\]]+\s+([A-Za-z0-9_]+)\s*\([^;]*\)\s*\{?$'),
    # Ruby
    re.compile(r'^\s*def\s+([A-Za-z0-9_?!]+)'),
]


def parse_generic(source: str) -> List[Symbol]:
    """
    Regex fallback: finds declaration lines, then closes each symbol's
    range either at the next declaration or a max of 80 lines later
    (whichever comes first) so chunks stay a reasonable size.
    """
    lines = source.splitlines()
    hits: List[Symbol] = []

    for i, line in enumerate(lines, start=1):
        for pattern in _GENERIC_PATTERNS:
            m = pattern.match(line)
            if m:
                name = next((g for g in reversed(m.groups()) if g and re.match(r'^[A-Za-z0-9_?!]+$', g)), "anonymous")
                hits.append(Symbol(name, "function", i, i))
                break

    symbols: List[Symbol] = []
    for idx, sym in enumerate(hits):
        next_start = hits[idx + 1].start_line if idx + 1 < len(hits) else len(lines) + 1
        end_line = min(next_start - 1, sym.start_line + 80)
        symbols.append(Symbol(sym.name, sym.kind, sym.start_line, max(end_line, sym.start_line)))

    return symbols


def parse_file(path: str, source: str) -> List[Symbol]:
    if path.endswith(".py"):
        return parse_python(source)
    return parse_generic(source)
