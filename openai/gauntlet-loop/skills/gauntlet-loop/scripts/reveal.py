#!/usr/bin/env python3
"""Reveal the blind A/B key for one Gauntlet round — after the verdict is committed.

Refuses to reveal until <round>/verdict.md contains a committed pick (WINNER:)
and a single named gap (GAP:). That refusal is the whole point: a verdict written
before the key is known cannot be retrofitted to whatever the answer turned out
to be, which is what makes an in-context critic worth anything.

On success it appends the reveal to verdict.md, writes <round>/outcome.json, and
appends one row to the run ledger in STATE.md so no model tokens go on bookkeeping.

Usage:
  reveal.py .gauntlet/<slug>/rounds/07
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WINNER_RE = re.compile(r"^[ \t]*(?:\*\*)?WINNER(?:\*\*)?:[ \t]*(A|B|TIE)\b", re.I | re.M)
GAP_RE = re.compile(r"^[ \t]*(?:\*\*)?GAP(?:\*\*)?:[ \t]*(\S.*?)[ \t]*$", re.I | re.M)
HEAD_RE = re.compile(r"^#\s*Round\s*(\S+)\s*(?:[—\-–]\s*(.*?))?\s*$", re.I | re.M)
LENS_RE = re.compile(r"lens:[ \t]*([^\n|—]+)", re.I)

LEDGER_HEADER = (
    "\n## Ledger\n\n"
    "| round | piece | lens | picked | outcome | gap sent back |\n"
    "|---|---|---|---|---|---|\n"
)


def parse_head(text: str) -> tuple[str, str]:
    """Return (piece, lens) from the verdict heading, best effort."""
    lens = ""
    m = LENS_RE.search(text)
    if m:
        lens = m.group(1).strip()
    piece = ""
    h = HEAD_RE.search(text)
    if h and h.group(2):
        tail = h.group(2)
        piece = re.split(r"[—\-–]|lens:", tail, maxsplit=1)[0].strip()
    return piece or "-", lens or "-"


def main() -> int:
    ap = argparse.ArgumentParser(description="Reveal a Gauntlet round's blind A/B key")
    ap.add_argument("round", help="round directory, e.g. .gauntlet/x/rounds/07")
    ap.add_argument("--verdict", default="verdict.md", help="verdict filename inside the round dir")
    args = ap.parse_args()

    rd = Path(args.round)
    verdict_path = rd / args.verdict
    key_path = rd / "ab" / "key.json"

    if not key_path.is_file():
        print(f"error: no blind pair here — {key_path} missing. Run ab.py first.", file=sys.stderr)
        return 2
    if not verdict_path.is_file():
        print(f"error: {verdict_path} does not exist.\n"
              "Commit the verdict before revealing: score both sides against RUBRIC.md, "
              "then write verdict.md with WINNER: and GAP: lines.", file=sys.stderr)
        return 1

    text = verdict_path.read_text()
    win = WINNER_RE.search(text)
    gap = GAP_RE.search(text)
    if not win:
        print("error: verdict.md has no committed pick. Add a line `WINNER: A` (or B, or TIE) "
              "before revealing.", file=sys.stderr)
        return 1
    if not gap:
        print("error: verdict.md names no gap. Add a line `GAP: <the single biggest gap>` — "
              "exactly one, so the next round has one target.", file=sys.stderr)
        return 1

    picked = win.group(1).upper()
    gap_text = gap.group(1).strip()
    key = json.loads(key_path.read_text())

    if picked == "TIE":
        outcome = "TIE"
        note = "Neither side clearly won this lens."
    else:
        role = key.get(picked, "?")
        outcome = "BAR WINS" if role == "reference" else "OURS WINS"
        note = f"You picked {picked}, which was the {role}."

    piece, lens = parse_head(text)

    with verdict_path.open("a") as fh:
        fh.write(
            f"\n## Reveal\n\n"
            f"- A = {key.get('A', '?')}\n"
            f"- B = {key.get('B', '?')}\n"
            f"- picked: {picked} → **{outcome}**\n"
            f"- {note}\n"
        )
        if outcome == "OURS WINS":
            fh.write(
                "- Self-recognition check: you built this candidate, so you may have recognised it "
                "rather than judged it. Re-read the rubric line you scored on — if your stated "
                "reason does not survive that re-read, treat this as BAR WINS and keep going.\n"
            )

    (rd / "outcome.json").write_text(json.dumps({
        "round": rd.name, "piece": piece, "lens": lens,
        "picked": picked, "outcome": outcome, "gap": gap_text,
        "A": key.get("A"), "B": key.get("B"),
    }, indent=2) + "\n")

    run_dir = rd.parent.parent
    state = run_dir / "STATE.md"
    short_gap = gap_text if len(gap_text) <= 90 else gap_text[:87].rstrip() + "…"
    short_gap = short_gap.replace("|", "\\|")
    row = f"| {rd.name} | {piece} | {lens} | {picked} | {outcome} | {short_gap} |\n"
    if state.is_file():
        body = state.read_text()
        if "## Ledger" not in body:
            body = body.rstrip("\n") + "\n" + LEDGER_HEADER
        state.write_text(body.rstrip("\n") + "\n" + row)
    else:
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(f"# Gauntlet run — {run_dir.name}\n" + LEDGER_HEADER + row)

    print(f"{outcome} — {note}")
    print(f"gap to close this round: {gap_text}")
    print(f"ledger updated: {state}")
    if outcome == "OURS WINS":
        print("Streak counts only if it holds across a full lens rotation — check STATE.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
