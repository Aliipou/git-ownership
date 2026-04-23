from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
from rich.console import Console

from .analyzer import OwnershipAnalyzer
from .heatmap import HeatmapRenderer
from .reporter import to_json, to_html

console = Console()


@click.group()
@click.version_option()
def main() -> None:
    """git-ownership — visualize who owns what in any Git repository."""


@main.command()
@click.argument("repo", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--format", "fmt", type=click.Choice(["table", "json", "html"]), default="table")
@click.option("--output", "-o", type=click.Path(), default=None, help="Write output to file")
@click.option("--top", default=20, show_default=True, help="Top N files to show")
@click.option("--since", default=None, help='Filter commits since date, e.g. "1 year ago"')
@click.option("--include", multiple=True, help="Include only files matching glob, e.g. '*.py'")
@click.option("--exclude", multiple=True, help="Exclude files matching glob")
@click.option("--max-files", default=5000, show_default=True, help="Cap files analyzed")
@click.option("-v", "--verbose", is_flag=True)
def analyze(
    repo: str,
    fmt: str,
    output: str | None,
    top: int,
    since: str | None,
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    max_files: int,
    verbose: bool,
) -> None:
    """Analyze code ownership in a Git repository."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    repo_path = Path(repo).resolve()
    with console.status(f"[cyan]Analysing {repo_path.name}…[/]"):
        analyzer = OwnershipAnalyzer(
            repo_path=repo_path,
            include_globs=list(include),
            exclude_globs=list(exclude) or None,
            since=since,
        )
        ownership = analyzer.analyze(max_files=max_files)

    if fmt == "json":
        result = to_json(ownership)
    elif fmt == "html":
        result = to_html(ownership)
    else:
        HeatmapRenderer(console).render(ownership, top_n=top)
        if not output:
            return
        result = to_json(ownership)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        console.print(f"[green]✓ Written to {output}[/]")
    else:
        click.echo(result)


@main.command()
@click.argument("repo", default=".", type=click.Path(exists=True, file_okay=False))
@click.argument("file")
@click.option("--since", default=None)
def file_detail(repo: str, file: str, since: str | None) -> None:
    """Show detailed ownership breakdown for a single file."""
    analyzer = OwnershipAnalyzer(Path(repo).resolve(), since=since)
    fo = analyzer._blame_file(file)
    if not fo:
        console.print(f"[red]Could not analyse {file}[/]")
        sys.exit(1)

    console.print(f"\n[bold cyan]{fo.path}[/] — {fo.total_lines} lines  Bus factor: [bold]{fo.bus_factor}[/]\n")
    for a in fo.authors:
        pct = a.lines / fo.total_lines * 100
        bar = "█" * int(pct / 2)
        console.print(f"  {a.name:<30} {pct:5.1f}%  {bar}")
