#!/usr/bin/env python3
"""Regenerate the live progress page for a Gauntlet run.

Scans <run>/rounds/*/ and emits a self-contained progress.html showing the bar,
the current standing, and every round's artifact in order so the work can be
watched evolving. Everything is embedded, so the file can be opened locally and
linked directly from the Codex final response.

Run this at the end of every round. It costs no model tokens — which is exactly
why the bookkeeping lives here and not in the conversation.

Usage:
  progress.py .gauntlet/<slug> [--open]
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
THUMB_PX = 560


def thumb_data_uri(src: Path, cache: Path, px: int = THUMB_PX) -> str | None:
    if src.suffix.lower() not in IMAGE_EXTS:
        return None
    cache.mkdir(parents=True, exist_ok=True)
    dst = cache / (src.parent.name + "-" + src.stem + ".png")
    made = False
    if shutil.which("sips"):
        try:
            subprocess.run(["sips", "-s", "format", "png", "-Z", str(px), str(src),
                            "--out", str(dst)], check=True, capture_output=True)
            made = True
        except subprocess.CalledProcessError:
            made = False
    payload = dst if made else src
    mime = "image/png" if made else (mimetypes.guess_type(payload.name)[0] or "image/png")
    return f"data:{mime};base64," + base64.b64encode(payload.read_bytes()).decode()


def text_preview(src: Path, limit: int = 700) -> str:
    try:
        body = src.read_text(errors="replace")
    except OSError:
        return ""
    return body[:limit] + ("\n…" if len(body) > limit else "")


def find_artifact(round_dir: Path) -> Path | None:
    for name in sorted(p.name for p in round_dir.glob("artifact.*")):
        return round_dir / name
    return None


def bar_summary(run: Path) -> tuple[str, str, Path | None]:
    """Return (goal, bar sentence, reference file) from BAR.md, best effort."""
    bar_md = run / "BAR.md"
    goal = bar = ""
    ref: Path | None = None
    if bar_md.is_file():
        text = bar_md.read_text(errors="replace")
        for label, pat in (("goal", r"^[ \t]*(?:\*\*)?GOAL(?:\*\*)?:[ \t]*(.+)$"),
                           ("bar", r"^[ \t]*(?:\*\*)?BAR(?:\*\*)?:[ \t]*(.+)$")):
            m = re.search(pat, text, re.I | re.M)
            if m:
                if label == "goal":
                    goal = m.group(1).strip()
                else:
                    bar = m.group(1).strip()
        m = re.search(r"^[ \t]*(?:\*\*)?REFERENCE(?:\*\*)?:[ \t]*(\S.+)$", text, re.I | re.M)
        if m:
            cand = (run / m.group(1).strip()).resolve()
            if cand.is_file():
                ref = cand
    if ref is None:
        for p in sorted((run / "ref").glob("*")):
            if p.suffix.lower() in IMAGE_EXTS:
                ref = p
                break
    return goal, bar, ref


CSS = """
:root{--bg:#fbfbfa;--fg:#1b1a17;--dim:#6b6862;--line:#e3e1dc;--card:#fff;
--win:#1f7a4d;--lose:#a5502a;--tie:#6b6862;--accent:#c8622a}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--fg:#eeece7;--dim:#98948c;
--line:#2c2b28;--card:#1c1b19;--win:#4ec78a;--lose:#e08a5a;--tie:#98948c;--accent:#e08a5a}}
:root[data-theme=dark]{--bg:#141413;--fg:#eeece7;--dim:#98948c;--line:#2c2b28;--card:#1c1b19;
--win:#4ec78a;--lose:#e08a5a;--tie:#98948c;--accent:#e08a5a}
:root[data-theme=light]{--bg:#fbfbfa;--fg:#1b1a17;--dim:#6b6862;--line:#e3e1dc;--card:#fff;
--win:#1f7a4d;--lose:#a5502a;--tie:#6b6862;--accent:#c8622a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 ui-sans-serif,-apple-system,
"Segoe UI",Roboto,sans-serif;-webkit-font-smoothing:antialiased;overflow-x:hidden}
.wrap{max-width:1080px;margin:0 auto;padding:40px 22px 72px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--dim);font-size:13px;margin:0 0 26px}
.meta{border-left:2px solid var(--accent);padding:2px 0 2px 14px;margin:0 0 30px}
.meta p{margin:0 0 6px}.meta .lbl{color:var(--dim);font-size:11px;text-transform:uppercase;
letter-spacing:.08em;display:block}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 34px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;min-width:96px}
.stat b{display:block;font-size:21px;font-variant-numeric:tabular-nums;line-height:1.2}
.stat span{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.06em}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--dim);
margin:34px 0 12px;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;
display:flex;flex-direction:column}
.card.ref{border-color:var(--accent)}
.card img{width:100%;height:auto;display:block;background:#0000000d}
.card pre{margin:0;padding:12px;font-size:11.5px;line-height:1.45;white-space:pre-wrap;
word-break:break-word;max-height:200px;overflow:auto;color:var(--dim)}
.body{padding:11px 13px 13px;display:flex;flex-direction:column;gap:6px}
.row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.rnd{font-variant-numeric:tabular-nums;font-weight:600}
.badge{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;padding:2px 7px;
border-radius:999px;border:1px solid var(--line);color:var(--dim);white-space:nowrap}
.b-win{color:var(--win);border-color:currentColor}
.b-lose{color:var(--lose);border-color:currentColor}
.b-tie{color:var(--tie)}
.gap{font-size:13px;color:var(--fg)}
.gap em{color:var(--dim);font-style:normal;font-size:11px;text-transform:uppercase;
letter-spacing:.06em;display:block;margin-bottom:1px}
ul.gaps{margin:0;padding-left:18px}ul.gaps li{margin-bottom:5px}
.empty{color:var(--dim);font-size:13px;border:1px dashed var(--line);border-radius:8px;padding:16px}
footer{color:var(--dim);font-size:11.5px;margin-top:44px;border-top:1px solid var(--line);padding-top:14px}
"""


def build(run: Path) -> Path:
    cache = run / ".thumbs"
    goal, bar, ref = bar_summary(run)
    rounds = sorted((p for p in (run / "rounds").glob("*") if p.is_dir()),
                    key=lambda p: p.name)

    entries = []
    for rd in rounds:
        oc = rd / "outcome.json"
        data = json.loads(oc.read_text()) if oc.is_file() else {}
        art = find_artifact(rd)
        entries.append({
            "round": rd.name,
            "piece": data.get("piece", "-"),
            "lens": data.get("lens", "-"),
            "outcome": data.get("outcome", "pending"),
            "gap": data.get("gap", ""),
            "img": thumb_data_uri(art, cache) if art else None,
            "text": text_preview(art) if art and art.suffix.lower() not in IMAGE_EXTS else "",
        })

    wins = sum(1 for e in entries if e["outcome"] == "OURS WINS")
    streak = 0
    for e in reversed(entries):
        if e["outcome"] == "OURS WINS":
            streak += 1
        elif e["outcome"] == "pending":
            continue
        else:
            break
    lenses = {e["lens"] for e in entries if e["lens"] not in ("-", "")}

    parts: list[str] = [
        f"<style>{CSS}</style>",
        '<div class="wrap">',
        f"<h1>Gauntlet run — {html.escape(run.name)}</h1>",
        f'<p class="sub">{len(entries)} rounds · regenerate with '
        f'<code>progress.py {html.escape(str(run))}</code></p>',
    ]
    if goal or bar:
        parts.append('<div class="meta">')
        if goal:
            parts.append(f'<p><span class="lbl">Goal</span>{html.escape(goal)}</p>')
        if bar:
            parts.append(f'<p><span class="lbl">The bar</span>{html.escape(bar)}</p>')
        parts.append("</div>")

    parts += [
        '<div class="stats">',
        f'<div class="stat"><b>{len(entries)}</b><span>rounds</span></div>',
        f'<div class="stat"><b>{wins}</b><span>ours won</span></div>',
        f'<div class="stat"><b>{streak}</b><span>win streak</span></div>',
        f'<div class="stat"><b>{len(lenses)}</b><span>lenses used</span></div>',
        "</div>",
    ]

    if ref:
        uri = thumb_data_uri(ref, cache)
        parts.append("<h2>The bar</h2>")
        parts.append('<div class="grid"><div class="card ref">')
        if uri:
            parts.append(f'<img alt="reference" src="{uri}">')
        parts.append(f'<div class="body"><div class="row"><span class="rnd">reference</span>'
                     f'<span class="badge">{html.escape(ref.name)}</span></div></div>')
        parts.append("</div></div>")

    parts.append("<h2>Rounds</h2>")
    if not entries:
        parts.append('<p class="empty">No rounds yet — capture an artifact, run ab.py, '
                     "commit a verdict.</p>")
    else:
        parts.append('<div class="grid">')
        for e in entries:
            cls = {"OURS WINS": "b-win", "BAR WINS": "b-lose"}.get(e["outcome"], "b-tie")
            parts.append('<div class="card">')
            if e["img"]:
                parts.append(f'<img alt="round {html.escape(e["round"])}" src="{e["img"]}">')
            elif e["text"]:
                parts.append(f"<pre>{html.escape(e['text'])}</pre>")
            parts.append('<div class="body"><div class="row">'
                         f'<span class="rnd">{html.escape(e["round"])}</span>'
                         f'<span class="badge {cls}">{html.escape(e["outcome"])}</span>'
                         f'<span class="badge">{html.escape(e["lens"])}</span>'
                         f'<span class="badge">{html.escape(e["piece"])}</span></div>')
            if e["gap"]:
                parts.append(f'<div class="gap"><em>gap sent back</em>{html.escape(e["gap"])}</div>')
            parts.append("</div></div>")
        parts.append("</div>")

    gaps_file = run / "open_gaps.md"
    if gaps_file.is_file():
        items = [ln.strip().lstrip("-*[ ]x").strip()
                 for ln in gaps_file.read_text(errors="replace").splitlines()
                 if ln.strip().startswith(("-", "*"))]
        items = [i for i in items if i]
        if items:
            parts.append("<h2>Open gaps</h2><ul class='gaps'>")
            parts += [f"<li>{html.escape(i)}</li>" for i in items]
            parts.append("</ul>")

    parts.append('<footer>Gauntlet Loop — sequential, one critic per round, one gap per round. '
                 "The bar does not have to be reachable; it has to stop us settling.</footer>")
    parts.append("</div>")

    out = run / "progress.html"
    out.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Gauntlet — {html.escape(run.name)}</title></head><body>"
        + "\n".join(parts) + "</body></html>\n"
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate a Gauntlet run's progress page")
    ap.add_argument("run", help="run directory, e.g. .gauntlet/<slug>")
    ap.add_argument("--open", action="store_true", help="open it in the browser")
    args = ap.parse_args()
    run = Path(args.run)
    if not run.is_dir():
        print(f"error: no such run directory: {run}", file=sys.stderr)
        return 2
    out = build(run)
    print(f"progress page: {out}")
    if args.open and shutil.which("open"):
        subprocess.run(["open", str(out)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
