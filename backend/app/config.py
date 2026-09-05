import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./data/app.db"
    chroma_persist_dir: str = "./data/chroma"
    # Local embedding model, loaded via fastembed (ONNX Runtime, no PyTorch).
    # bge-small-en-v1.5 is fastembed's small, fast default -- ~130MB on
    # first download, low runtime memory footprint (unlike the previous
    # sentence-transformers/PyTorch setup, which was getting OOM-killed on
    # memory-capped hosts the moment the model actually loaded).
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    clone_dir: str = "./data/repos"
    top_k: int = 5

    # File extensions we attempt to parse/index
    supported_extensions: tuple = (
        ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go",
        ".rs", ".rb", ".php", ".c", ".cpp", ".h", ".hpp", ".cs",
        ".md", ".mdx", ".rst", ".json", ".yaml", ".yml", ".toml",
        ".ini", ".cfg", ".sql", ".sh", ".html", ".css", ".scss",
    )

    # Directories we never walk into
    ignored_dirs: tuple = (
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", "target", ".idea", ".vscode",
        "vendor", "coverage",
    )

    max_file_size_bytes: int = 500_000  # skip huge generated files


settings = Settings()

os.makedirs(os.path.dirname(settings.database_url.replace("sqlite:///", "")) or ".", exist_ok=True) \
    if settings.database_url.startswith("sqlite") else None
os.makedirs(settings.chroma_persist_dir, exist_ok=True)
os.makedirs(settings.clone_dir, exist_ok=True)
