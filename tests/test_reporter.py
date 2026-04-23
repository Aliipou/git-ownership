import json
from pathlib import Path
from git_ownership.models import AuthorStats, FileOwnership, RepoOwnership
from git_ownership.reporter import to_json, to_html


def _make_repo() -> RepoOwnership:
    repo = RepoOwnership(repo_path=Path("/fake/repo"))
    alice = AuthorStats(name="Alice", email="alice@test.com")
    alice.lines = 80
    alice.files = {"main.py"}
    alice.commits = {"abc123"}
    bob = AuthorStats(name="Bob", email="bob@test.com")
    bob.lines = 20
    bob.files = {"utils.py"}
    bob.commits = {"def456"}
    repo.global_authors = {"alice@test.com": alice, "bob@test.com": bob}
    repo.files = [FileOwnership("main.py", 100, [alice, bob])]
    return repo


def test_to_json_valid():
    repo = _make_repo()
    output = to_json(repo)
    data = json.loads(output)
    assert data["summary"]["total_lines"] == 100
    assert data["summary"]["unique_authors"] == 2
    assert data["authors"][0]["name"] == "Alice"
    assert data["authors"][0]["ownership_pct"] == 80.0


def test_to_json_has_files():
    data = json.loads(to_json(_make_repo()))
    assert len(data["files"]) == 1
    assert data["files"][0]["path"] == "main.py"


def test_to_html_contains_name():
    html = to_html(_make_repo())
    assert "Alice" in html
    assert "git-ownership" in html
    assert "repo" in html


def test_to_html_valid_structure():
    html = to_html(_make_repo())
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
