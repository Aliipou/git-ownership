from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
from rich.text import Text
from rich import box

from .models import RepoOwnership, FileOwnership

PALETTE = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
]


class HeatmapRenderer:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def render(self, ownership: RepoOwnership, top_n: int = 20) -> None:
        self._render_header(ownership)
        self._render_global_table(ownership)
        self._render_file_table(ownership, top_n)
        self._render_bus_factor(ownership)

    def _render_header(self, o: RepoOwnership) -> None:
        self.console.print(Panel(
            f"[bold white]Repository:[/] {o.repo_path.name}\n"
            f"[bold white]Files analysed:[/] {len(o.files):,}\n"
            f"[bold white]Total lines:[/] {o.total_lines:,}\n"
            f"[bold white]Unique authors:[/] {len(o.global_authors)}",
            title="[bold cyan]git-ownership[/]",
            border_style="cyan",
        ))

    def _render_global_table(self, o: RepoOwnership) -> None:
        table = Table(title="Global Ownership", box=box.ROUNDED, show_lines=True)
        table.add_column("Author", style="bold")
        table.add_column("Lines", justify="right")
        table.add_column("Ownership", justify="right")
        table.add_column("Files", justify="right")
        table.add_column("Commits", justify="right")
        table.add_column("Bar", min_width=20)

        authors = sorted(o.global_authors.values(), key=lambda x: x.lines, reverse=True)
        total = o.total_lines or 1

        for i, author in enumerate(authors[:15]):
            pct = author.lines / total * 100
            bar_len = int(pct / 5)
            color = PALETTE[i % len(PALETTE)]
            bar = Text("█" * bar_len, style=color)
            table.add_row(
                f"[{color}]{author.name}[/]",
                f"{author.lines:,}",
                f"{pct:.1f}%",
                str(len(author.files)),
                str(len(author.commits)),
                bar,
            )

        self.console.print(table)

    def _render_file_table(self, o: RepoOwnership, top_n: int) -> None:
        risky = sorted(o.files, key=lambda f: f.bus_factor)[:top_n]
        table = Table(title=f"Top {top_n} Files by Bus Factor Risk", box=box.ROUNDED, show_lines=True)
        table.add_column("File", overflow="fold")
        table.add_column("Owner", style="bold cyan")
        table.add_column("Ownership %", justify="right")
        table.add_column("Bus Factor", justify="center")
        table.add_column("Lines", justify="right")

        for f in risky:
            owner = f.primary_owner
            if not owner:
                continue
            pct = owner.lines / f.total_lines * 100 if f.total_lines else 0
            bf = f.bus_factor
            bf_style = "red" if bf == 1 else "yellow" if bf == 2 else "green"
            table.add_row(
                f.path,
                owner.name,
                f"{pct:.0f}%",
                f"[{bf_style}]{bf}[/]",
                str(f.total_lines),
            )

        self.console.print(table)

    def _render_bus_factor(self, o: RepoOwnership) -> None:
        bf = o.bus_factor
        color = "red bold" if bf <= 2 else "yellow" if bf <= 4 else "green"
        self.console.print(Panel(
            f"[{color}]Repository Bus Factor: {bf}[/]\n"
            f"[dim]{bf} developer(s) account for 50%+ of all code.[/dim]",
            border_style="cyan",
        ))
