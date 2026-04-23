from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from .models import RepoOwnership


def to_json(ownership: RepoOwnership, indent: int = 2) -> str:
    data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "repo": str(ownership.repo_path),
        "summary": {
            "total_files": len(ownership.files),
            "total_lines": ownership.total_lines,
            "unique_authors": len(ownership.global_authors),
            "bus_factor": ownership.bus_factor,
        },
        "authors": [
            {
                "name": a.name,
                "email": a.email,
                "lines": a.lines,
                "ownership_pct": round(a.lines / ownership.total_lines * 100, 2)
                if ownership.total_lines else 0,
                "files": len(a.files),
                "commits": len(a.commits),
            }
            for a in sorted(ownership.global_authors.values(), key=lambda x: x.lines, reverse=True)
        ],
        "files": [
            {
                "path": f.path,
                "total_lines": f.total_lines,
                "bus_factor": f.bus_factor,
                "primary_owner": f.primary_owner.name if f.primary_owner else None,
                "authors": [
                    {
                        "name": a.name,
                        "lines": a.lines,
                        "pct": round(a.lines / f.total_lines * 100, 1) if f.total_lines else 0,
                    }
                    for a in f.authors[:5]
                ],
            }
            for f in ownership.files
        ],
    }
    return json.dumps(data, indent=indent)


def to_html(ownership: RepoOwnership) -> str:
    total = ownership.total_lines or 1
    authors = sorted(ownership.global_authors.values(), key=lambda x: x.lines, reverse=True)
    rows = ""
    colors = ["#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7","#DDA0DD","#98D8C8"]
    for i, a in enumerate(authors[:20]):
        pct = a.lines / total * 100
        color = colors[i % len(colors)]
        rows += (
            f"<tr><td style='color:{color};font-weight:bold'>{a.name}</td>"
            f"<td>{a.lines:,}</td><td>{pct:.1f}%</td>"
            f"<td>{len(a.files)}</td><td>{len(a.commits)}</td>"
            f"<td><div style='background:{color};width:{pct*2:.0f}px;height:14px;border-radius:3px'></div></td></tr>\n"
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>git-ownership — {ownership.repo_path.name}</title>
<style>
  body{{font-family:system-ui,sans-serif;background:#0d1117;color:#c9d1d9;padding:2rem}}
  h1{{color:#58a6ff}}h2{{color:#8b949e;font-size:1rem;font-weight:normal}}
  table{{border-collapse:collapse;width:100%;margin:1rem 0}}
  th{{background:#161b22;padding:.6rem 1rem;text-align:left;color:#8b949e}}
  td{{padding:.5rem 1rem;border-bottom:1px solid #21262d}}
  .badge{{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:.2rem .6rem;font-size:.85rem}}
</style></head>
<body>
  <h1>git-ownership: {ownership.repo_path.name}</h1>
  <p>
    <span class="badge">📄 {len(ownership.files):,} files</span>
    <span class="badge">📝 {ownership.total_lines:,} lines</span>
    <span class="badge">👤 {len(ownership.global_authors)} authors</span>
    <span class="badge">🚌 Bus factor: {ownership.bus_factor}</span>
  </p>
  <table>
    <thead><tr><th>Author</th><th>Lines</th><th>Ownership</th><th>Files</th><th>Commits</th><th>Bar</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body></html>"""
