import os
import shutil
import tempfile

import git

from app.config import settings


def clone_repository(repo_url: str, repo_id: str) -> str:
    """
    Clones a public GitHub repository into a dedicated folder under
    settings.clone_dir and returns the local path.
    Raises git.exc.GitCommandError on failure (bad URL, private repo, etc).
    """
    dest = os.path.join(settings.clone_dir, repo_id)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)

    git.Repo.clone_from(repo_url, dest, depth=1)
    return dest


def cleanup_repository(local_path: str) -> None:
    if os.path.exists(local_path):
        shutil.rmtree(local_path, ignore_errors=True)
