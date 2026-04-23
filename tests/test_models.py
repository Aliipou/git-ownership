from pathlib import Path
from git_ownership.models import AuthorStats, FileOwnership, RepoOwnership


def make_author(name: str, lines: int) -> AuthorStats:
    a = AuthorStats(name=name, email=f"{name}@test.com")
    a.lines = lines
    a.files = {f"{name}.py"}
    return a


def test_file_ownership_primary_owner():
    alice = make_author("alice", 80)
    bob = make_author("bob", 20)
    fo = FileOwnership(path="main.py", total_lines=100, authors=[alice, bob])
    assert fo.primary_owner.name == "alice"


def test_file_ownership_bus_factor_single():
    alice = make_author("alice", 100)
    fo = FileOwnership(path="main.py", total_lines=100, authors=[alice])
    assert fo.bus_factor == 1


def test_file_ownership_bus_factor_shared():
    alice = make_author("alice", 30)
    bob = make_author("bob", 30)
    carol = make_author("carol", 40)
    fo = FileOwnership(path="main.py", total_lines=100, authors=[carol, alice, bob])
    assert fo.bus_factor == 2


def test_repo_ownership_total_lines():
    alice = make_author("alice", 60)
    bob = make_author("bob", 40)
    f1 = FileOwnership("a.py", 60, [alice])
    f2 = FileOwnership("b.py", 40, [bob])
    repo = RepoOwnership(repo_path=Path("."), files=[f1, f2])
    assert repo.total_lines == 100


def test_repo_bus_factor():
    repo = RepoOwnership(repo_path=Path("."))
    a = AuthorStats(name="alice", email="alice@test.com")
    a.lines = 60
    b = AuthorStats(name="bob", email="bob@test.com")
    b.lines = 40
    repo.global_authors = {"alice@test.com": a, "bob@test.com": b}
    repo.files = [FileOwnership("x.py", 100, [a, b])]
    assert repo.bus_factor == 1


def test_author_stats_defaults():
    a = AuthorStats(name="dev", email="dev@test.com")
    assert a.lines == 0
    assert len(a.files) == 0
    assert len(a.commits) == 0
