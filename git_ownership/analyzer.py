from __future__ import annotations

import logging
from pathlib import Path
from collections import defaultdict

import git
from git.exc import GitCommandError

from .models import AuthorStats, FileOwnership, RepoOwnership

logger = logging.getLogger(__name__)

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf", ".zip",
    ".tar", ".gz", ".bin", ".exe", ".dll", ".so", ".dylib", ".woff",
    ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".wav", ".db", ".sqlite",
}


class OwnershipAnalyzer:
    def __init__(
        self,
        repo_path: Path,
        include_globs: list[str] | None = None,
        exclude_globs: list[str] | None = None,
        since: str | None = None,
    ) -> None:
        self.repo_path = repo_path
        self.include_globs = include_globs or []
        self.exclude_globs = exclude_globs or ["*.min.js", "vendor/*", "node_modules/*"]
        self.since = since
        self._repo = git.Repo(repo_path)

    def analyze(self, max_files: int = 5000) -> RepoOwnership:
        result = RepoOwnership(repo_path=self.repo_path)
        files = self._collect_files(max_files)
        logger.info("Analyzing %d files in %s", len(files), self.repo_path)

        for rel_path in files:
            try:
                file_ownership = self._blame_file(rel_path)
                if file_ownership:
                    result.files.append(file_ownership)
                    for author in file_ownership.authors:
                        key = author.email
                        if key not in result.global_authors:
                            result.global_authors[key] = AuthorStats(
                                name=author.name, email=author.email
                            )
                        g = result.global_authors[key]
                        g.lines += author.lines
                        g.files |= author.files
                        g.commits |= author.commits
            except (GitCommandError, ValueError, UnicodeDecodeError) as exc:
                logger.debug("Skipping %s: %s", rel_path, exc)

        total = result.total_lines
        for author in result.global_authors.values():
            object.__setattr__(
                author, "ownership_pct", (author.lines / total * 100) if total else 0.0
            )
        return result

    def _collect_files(self, max_files: int) -> list[str]:
        try:
            tracked = self._repo.git.ls_files().splitlines()
        except GitCommandError:
            return []

        result = []
        for path in tracked:
            if len(result) >= max_files:
                break
            p = Path(path)
            if p.suffix.lower() in BINARY_EXTENSIONS:
                continue
            if self.include_globs and not any(p.match(g) for g in self.include_globs):
                continue
            if any(p.match(g) for g in self.exclude_globs):
                continue
            result.append(path)
        return result

    def _blame_file(self, rel_path: str) -> FileOwnership | None:
        kwargs: dict = {"incremental": True}
        if self.since:
            kwargs["since"] = self.since

        blame = self._repo.blame_incremental("HEAD", rel_path, **kwargs)
        author_map: dict[str, AuthorStats] = defaultdict(
            lambda: AuthorStats(name="", email="")
        )
        total = 0

        for blame_entry in blame:
            commit = blame_entry.commit
            email = commit.author.email or "unknown@unknown"
            name = commit.author.name or "Unknown"
            lines = len(blame_entry.linenos)

            if email not in author_map:
                author_map[email] = AuthorStats(name=name, email=email)
            a = author_map[email]
            a.lines += lines
            a.files.add(rel_path)
            a.commits.add(commit.hexsha[:8])
            total += lines

        if total == 0:
            return None

        authors = sorted(author_map.values(), key=lambda x: x.lines, reverse=True)
        return FileOwnership(path=rel_path, total_lines=total, authors=authors)
