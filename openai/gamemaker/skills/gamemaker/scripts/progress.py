#!/usr/bin/env python3
"""Regenerate the run's progress page.

One self-contained HTML file showing the ladder, the scope contract, the round
ledger and what still loses to the bar. Cheap to produce and it is the report —
narrating each round to the user in prose costs tokens and says less.

Usage:
  progress.py .gamemaker/<slug>
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True   # no __pycache__ inside the skill directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from next import (  # noqa: E402  — same directory, single source of truth for parsing
    field, is_blocked, parse_contract, parse_ladder, parse_named, placeholders,
    read, section, PLACEHOLDER,
)

CSS = """
:root { color-scheme: light dark;
  --bg:#fbfbfa; --fg:#1a1a19; --dim:#6b6b68; --line:#e3e3e0; --card:#fff;
  --ok:#2f7d4f; --now:#b45309; --wait:#9a9a96; --bad:#b3261e; }
@media (prefers-color-scheme: dark) { :root {
  --bg:#17171a; --fg:#e8e8e6; --dim:#9a9a96; --line:#2c2c30; --card:#1e1e22;
  --ok:#5cc98a; --now:#e0a44a; --wait:#66666a; --bad:#f2776b; } }
:root[data-theme="dark"] {
  --bg:#17171a; --fg:#e8e8e6; --dim:#9a9a96; --line:#2c2c30; --card:#1e1e22;
  --ok:#5cc98a; --now:#e0a44a; --wait:#66666a; --bad:#f2776b; }
:root[data-theme="light"] {
  --bg:#fbfbfa; --fg:#1a1a19; --dim:#6b6b68; --line:#e3e3e0; --card:#fff;
  --ok:#2f7d4f; --now:#b45309; --wait:#9a9a96; --bad:#b3261e; }
* { box-sizing:border-box; }
body { margin:0; padding:2.5rem 1.25rem 5rem; background:var(--bg); color:var(--fg);
  font:15px/1.6 ui-sans-serif,-apple-system,"Segoe UI",Roboto,sans-serif; }
main { max-width:60rem; margin:0 auto; }
h1 { font-size:1.6rem; margin:0 0 .25rem; letter-spacing:-.01em; }
h2 { font-size:.78rem; text-transform:uppercase; letter-spacing:.09em;
  color:var(--dim); margin:2.75rem 0 .85rem; font-weight:600; }
.sub { color:var(--dim); margin:0 0 .4rem; }
.pill { display:inline-block; border:1px solid var(--line); border-radius:999px;
  padding:.1rem .55rem; margin:.15rem .25rem .15rem 0; font-size:.8rem; }
.stage { background:var(--card); border:1px solid var(--line); border-radius:10px;
  padding:.7rem .9rem; margin-bottom:.5rem; }
.stage.now { border-color:var(--now); box-shadow:0 0 0 1px var(--now) inset; }
.stage .hd { display:flex; gap:.6rem; align-items:baseline; }
.num { font-variant-numeric:tabular-nums; color:var(--dim); font-size:.85rem; }
.nm { font-weight:600; }
.st { margin-left:auto; font-size:.78rem; text-transform:uppercase;
  letter-spacing:.06em; }
.st.done{color:var(--ok);} .st.now{color:var(--now);} .st.wait{color:var(--wait);}
ul.gates { list-style:none; margin:.5rem 0 0; padding:0; font-size:.9rem; }
ul.gates li { color:var(--dim); padding:.1rem 0 .1rem 1.35rem; text-indent:-1.35rem; }
ul.gates li.on { color:var(--fg); }
ul.gates li.bl { color:var(--bad); }
table { width:100%; border-collapse:collapse; font-size:.88rem; }
th { text-align:left; font-weight:600; color:var(--dim); font-size:.78rem;
  text-transform:uppercase; letter-spacing:.06em; padding:.35rem .5rem; }
td { padding:.35rem .5rem; border-top:1px solid var(--line); vertical-align:top; }
td.n { font-variant-numeric:tabular-nums; white-space:nowrap; }
.wrap { overflow-x:auto; }
.bar { height:6px; background:var(--line); border-radius:3px; overflow:hidden;
  margin:.3rem 0 .1rem; }
.bar > i { display:block; height:100%; background:var(--ok); }
.ok{color:var(--ok);} .bad{color:var(--bad);} .dim{color:var(--dim);}
.empty { color:var(--dim); font-style:italic; }
li { margin:.15rem 0; }
"""


def esc(s: str) -> str:
    return html.escape(str(s), quote=False)


def load_rounds(run: Path) -> list[dict]:
    out = []
    for d in sorted((run / "rounds").glob("*")):
        f = d / "outcome.json"
        if f.is_file():
            try:
                out.append(json.loads(f.read_text()))
            except json.JSONDecodeError:
                pass
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: progress.py .gamemaker/<slug>", file=sys.stderr)
        return 2
    run = Path(sys.argv[1])
    if not run.is_dir():
        print(f"error: no such run: {run}", file=sys.stderr)
        return 2

    state = read(run / "STATE.md")
    ladder = parse_ladder(read(run / "LADDER.md"))
    contract = parse_contract(read(run / "CONTRACT.md"))
    rounds = load_rounds(run)
    pillars = [n for n, _ in parse_named(section(read(run / "PILLARS.md"), "Pillars"))
               if not PLACEHOLDER.fullmatch(n)]
    anti = [re.sub(r"^-\s*", "", l).strip()
            for l in section(read(run / "PILLARS.md"), "Anti-pillars").splitlines()
            if l.strip().startswith("- ") and not PLACEHOLDER.fullmatch(
                re.sub(r"^-\s*", "", l).strip())]

    # stage status
    current = None
    for st in ladder:
        gaps = sum(len(placeholders(read(run / f))) for f in st["files"])
        st["gaps"] = gaps
        st["open"] = [g for g in st["gates"] if not g["done"] and not is_blocked(g["text"])]
        if current is None and (gaps or st["open"]):
            current = st["num"]

    parts: list[str] = []
    parts.append(f"<h1>{esc(field(state, 'AMBITION') or run.name)}</h1>")
    parts.append(f"<p class=sub>reference: {esc(field(state, 'REFERENCE') or '—')} · "
                 f"scale: {esc(field(state, 'SCALE') or '—')} · "
                 f"stage: {current if current is not None else 'all closed'} · "
                 f"rounds: {len(rounds)}</p>")
    if pillars:
        parts.append("<p>" + "".join(f"<span class=pill>{esc(p)}</span>" for p in pillars) + "</p>")
    if anti:
        parts.append("<p class=sub>never: " + esc(" · ".join(anti)) + "</p>")

    # ladder
    parts.append("<h2>Ladder</h2>")
    for st in ladder:
        if current is None or st["num"] < current:
            cls, label = "done", "closed"
        elif st["num"] == current:
            cls, label = "now", "in progress"
        else:
            cls, label = "wait", "not started"
        here = "now" if cls == "now" else ""
        parts.append(f"<div class='stage {here}'>"
                     f"<div class=hd><span class=num>{st['num']}</span>"
                     f"<span class=nm>{esc(st['name'])}</span>"
                     f"<span class='st {cls}'>{label}</span></div>")
        if cls != "wait":
            items = []
            if st["gaps"]:
                items.append(f"<li class=on>{st['gaps']} placeholder(s) left in "
                             f"{esc(', '.join(st['files']))}</li>")
            for g in st["gates"]:
                if is_blocked(g["text"]):
                    k = "bl"
                elif g["done"]:
                    k = ""
                else:
                    k = "on"
                mark = "▪" if k == "bl" else ("✓" if g["done"] else "○")
                items.append(f"<li class='{k}'>{mark} {esc(g['text'])}</li>")
            if items:
                parts.append("<ul class=gates>" + "".join(items) + "</ul>")
        parts.append("</div>")

    # contract
    real = [c for c in contract if not PLACEHOLDER.search(c["text"])]
    parts.append("<h2>Scope contract</h2>")
    if not real:
        parts.append("<p class=empty>Not written yet — stage 0 does not close without it.</p>")
    else:
        met = sum(1 for c in real if c["done"] or is_blocked(c["text"]))
        pct = int(100 * met / len(real))
        parts.append(f"<div class=bar><i style='width:{pct}%'></i></div>"
                     f"<p class=sub>{met}/{len(real)} met or blocked</p><ul class=gates>")
        for c in real:
            k = "bl" if is_blocked(c["text"]) else ("" if c["done"] else "on")
            mark = "▪" if k == "bl" else ("✓" if c["done"] else "○")
            parts.append(f"<li class='{k}'>{mark} {esc(c['text'])}</li>")
        parts.append("</ul>")

    # activity — rounds grouped into firings by timestamp gap, so a run worked in
    # bursts (a loop overnight, an afternoon session) reads as bursts. This plus
    # `git log` is the whole review; a no-op count above zero is the thing to ask
    # the run about.
    stamped = []
    for r in rounds:
        try:
            stamped.append((datetime.fromisoformat(r["ts"]), r))
        except (KeyError, TypeError, ValueError):
            pass
    if stamped:
        groups: list[list] = []
        for ts, r in stamped:
            if not groups or (ts - groups[-1][-1][0]).total_seconds() > 3600:
                groups.append([])
            groups[-1].append((ts, r))
        parts.append("<h2>Activity</h2>")
        rows = []
        for g in reversed(groups[-14:]):
            rs = [r for _, r in g]
            types: dict[str, int] = {}
            for r in rs:
                types[r.get("type", "?")] = types.get(r.get("type", "?"), 0) + 1
            wins = sum(1 for r in rs if r.get("outcome") == "OURS WINS")
            fails = sum(1 for r in rs if r.get("gates_failed"))
            noop = sum(1 for r in rs if r.get("src_changed") is False)
            files: set[str] = set()
            for r in rs:
                files.update(r.get("files_changed") or [])
            label = g[0][0].strftime("%d %b %H:%M") + g[-1][0].strftime("–%H:%M")
            rows.append(f"<tr><td class=n>{esc(label)}</td><td class=n>{len(rs)}</td>"
                        f"<td>{esc(' · '.join(f'{k}×{v}' for k, v in types.items()))}</td>"
                        f"<td class='n ok'>{wins or '—'}</td>"
                        f"<td class='n {'bad' if fails else 'dim'}'>{fails or '—'}</td>"
                        f"<td class='n {'bad' if noop else 'dim'}'>{noop or '—'}</td>"
                        f"<td class=n>{len(files) or '—'}</td></tr>")
        parts.append("<div class=wrap><table><thead><tr><th>firing</th><th>rounds</th>"
                     "<th>types</th><th>wins</th><th>gate fails</th><th>no-op</th>"
                     "<th>files touched</th></tr></thead><tbody>"
                     + "".join(rows) + "</tbody></table></div>")

    # ledger
    parts.append("<h2>Rounds</h2>")
    if not rounds:
        parts.append("<p class=empty>No rounds logged yet.</p>")
    else:
        rows = []
        for r in reversed(rounds):
            res = r.get("outcome") or ("GATES FAILED" if r.get("gates_failed") else "done")
            k = "bad" if res in ("GATES FAILED",) else ("ok" if res == "OURS WINS" else "dim")
            rows.append(f"<tr><td class=n>{esc(r.get('round', ''))}</td>"
                        f"<td class=n>{esc(r.get('type', ''))}</td>"
                        f"<td>{esc(r.get('facet') or '—')}</td>"
                        f"<td>{esc(r.get('lens') or '—')}</td>"
                        f"<td class='n {k}'>{esc(res)}</td>"
                        f"<td>{esc(r.get('gap') or r.get('did') or '')}</td></tr>")
        parts.append("<div class=wrap><table><thead><tr><th>#</th><th>type</th><th>facet</th>"
                     "<th>lens</th><th>result</th><th>gap / built</th></tr></thead><tbody>"
                     + "".join(rows) + "</tbody></table></div>")

    # what still loses
    gaps_txt = read(run / "open_gaps.md")
    lines = [l.strip() for l in gaps_txt.splitlines()
             if l.strip().startswith(("-", "BLOCKED:")) and len(l.strip()) > 3]
    parts.append("<h2>Still losing to the bar</h2>")
    if lines:
        parts.append("<ul>" + "".join(
            f"<li class='{'bad' if 'BLOCKED:' in l else ''}'>{esc(l.lstrip('- '))}</li>"
            for l in lines[:40]) + "</ul>")
    else:
        parts.append("<p class=empty>Nothing queued. On a real run that usually means the "
                     "queue is not being written, not that nothing is wrong.</p>")

    out = run / "progress.html"
    out.write_text(
        "<!doctype html><html><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>gamemaker — {esc(run.name)}</title><style>{CSS}</style></head>"
        f"<body><main>{''.join(parts)}</main></body></html>\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
