from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AuthorStats:
    name: str
    email: str
    lines: int = 0
    files: set[str] = field(default_factory=set)
    commits: set[str] = field(default_factory=set)

    @property
    def ownership_pct(self) -> float:
        return 0.0  # set externally after aggregation


@dataclass
class FileOwnership:
    path: str
    total_lines: int
    authors: list[AuthorStats]

    @property
    def primary_owner(self) -> AuthorStats | None:
        return self.authors[0] if self.authors else None

    @property
    def bus_factor(self) -> int:
        """Minimum authors needed to cover 50% of the file."""
        if not self.authors:
            return 0
        threshold = self.total_lines * 0.5
        cumulative = 0
        for i, a in enumerate(sorted(self.authors, key=lambda x: x.lines, reverse=True), 1):
            cumulative += a.lines
            if cumulative >= threshold:
                return i
        return len(self.authors)


@dataclass
class RepoOwnership:
    repo_path: Path
    files: list[FileOwnership] = field(default_factory=list)
    global_authors: dict[str, AuthorStats] = field(default_factory=dict)

    @property
    def total_lines(self) -> int:
        return sum(f.total_lines for f in self.files)

    @property
    def bus_factor(self) -> int:
        if not self.global_authors:
            return 0
        threshold = self.total_lines * 0.5
        cumulative = 0
        for i, a in enumerate(
            sorted(self.global_authors.values(), key=lambda x: x.lines, reverse=True), 1
        ):
            cumulative += a.lines
            if cumulative >= threshold:
                return i
        return len(self.global_authors)
