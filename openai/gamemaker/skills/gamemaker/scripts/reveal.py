#!/usr/bin/env python3
"""Close out one gamemaker round: check the verdict, reveal the key, write the ledger.

Run this at the end of every round, whatever its type. It is the only bookkeeping
command a firing has to remember.

**Polish rounds** (a blind pair exists) are held to commit-then-reveal: the key
stays sealed until verdict.md carries a committed pick (`WINNER:`) and exactly one
named gap (`GAP:`). That refusal is the whole point — a verdict written before the
answer is known cannot be bent to fit it afterwards, which is what makes an
in-context critic worth anything at all.

**Build, fill and ship rounds** have no pair to reveal; they are held to a
different standard: say what was built and whether the gates passed. A round that
cannot state both did not happen.

Either way it writes <round>/outcome.json and appends a row to the ledger in
STATE.md, so no model tokens go on bookkeeping and round 34 gets it as right as
round 2.

Usage:
  reveal.py .gamemaker/<slug>/rounds/07
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WINNER_RE = re.compile(r"^[ \t]*(?:\*\*)?WINNER(?:\*\*)?:[ \t]*(A|B|TIE)\b", re.I | re.M)
GAP_RE = re.compile(r"^[ \t]*(?:\*\*)?GAP(?:\*\*)?:[ \t]*(\S.*?)[ \t]*$", re.I | re.M)
DID_RE = re.compile(r"^[ \t]*(?:\*\*)?DID(?:\*\*)?:[ \t]*(\S.*?)[ \t]*$", re.I | re.M)
GATES_RE = re.compile(r"^[ \t]*(?:\*\*)?GATES(?:\*\*)?:[ \t]*(\S.*?)[ \t]*$", re.I | re.M)
HEAD_RE = re.compile(r"^#\s*Round\s*(\S+)\s*(.*)$", re.I | re.M)
TYPE_RE = re.compile(r"\b(BUILD|FILL|POLISH|SHIP)\b", re.I)
FACET_RE = re.compile(r"facet:[ \t]*([a-zA-Zа-яА-Я]+)", re.I)
LENS_RE = re.compile(r"lens:[ \t]*([^\n|—]+)", re.I)

LEDGER_HEADER = (
    "\n## Ledger\n\n"
    "| round | type | facet | lens | result | gap / what was built |\n"
    "|---|---|---|---|---|---|\n"
)

# What counts as "the game changed" — anything outside these is overhead.
# The distinction feeds next.py's NO-OP STREAK: three rounds that only touched
# harness, tests or docs is a run polishing its own scaffolding.
OVERHEAD = re.compile(r"^(\.gamemaker/|\.claude/|tests?/|tools/|docs/)|\.md$")


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def snapshot(rd: Path, message: str, autocommit: bool) -> dict:
    """Commit the round's work (if enabled) and report what changed.

    Returns {} outside a repo. files_changed is the per-round diff when a commit
    was made, or the uncommitted set otherwise; src_changed says whether any of
    it was the game rather than scaffolding.
    """
    top = git(rd, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return {}
    root = Path(top.stdout.strip())
    files: list[str] = []
    committed = False
    if autocommit:
        git(root, "add", "-A")
        c = git(root, "commit", "-m", message)
        committed = c.returncode == 0
        if committed:
            out = git(root, "show", "--name-only", "--format=").stdout
            files = [l.strip() for l in out.splitlines() if l.strip()]
        # nothing to commit → files stays [], which is the honest reading
    else:
        out = git(root, "status", "--porcelain").stdout
        files = [l[3:].strip() for l in out.splitlines() if l.strip()]
    return {
        "committed": committed,
        "files_changed": files,
        "src_changed": any(not OVERHEAD.search(f) for f in files),
    }


def parse_head(text: str) -> tuple[str, str, str]:
    """(type, facet, lens) from the verdict heading, best effort."""
    h = HEAD_RE.search(text)
    tail = h.group(2) if h else ""
    t = TYPE_RE.search(tail) or TYPE_RE.search(text[:400])
    f = FACET_RE.search(tail) or FACET_RE.search(text[:400])
    l = LENS_RE.search(tail) or LENS_RE.search(text[:400])
    return (t.group(1).upper() if t else "BUILD",
            f.group(1).lower() if f else "",
            l.group(1).strip() if l else "")


def append_ledger(run_dir: Path, row: str) -> Path:
    state = run_dir / "STATE.md"
    if state.is_file():
        body = state.read_text()
        if "## Ledger" not in body:
            body = body.rstrip("\n") + "\n" + LEDGER_HEADER
        state.write_text(body.rstrip("\n") + "\n" + row)
    else:
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(f"# gamemaker run — {run_dir.name}\n" + LEDGER_HEADER + row)
    return state


def cell(s: str, n: int = 90) -> str:
    s = s if len(s) <= n else s[: n - 3].rstrip() + "…"
    return s.replace("|", "\\|")


def main() -> int:
    ap = argparse.ArgumentParser(description="Close out one gamemaker round")
    ap.add_argument("round", help="round directory, e.g. .gamemaker/x/rounds/07")
    ap.add_argument("--verdict", default="verdict.md",
                    help="verdict filename inside the round dir")
    args = ap.parse_args()

    rd = Path(args.round)
    verdict_path = rd / args.verdict
    key_path = rd / "ab" / "key.json"
    run_dir = rd.parent.parent

    if not verdict_path.is_file():
        print(f"error: {verdict_path} does not exist.\n"
              "Every round writes a verdict before it is logged — that is what makes the\n"
              "ledger worth reading in the morning.", file=sys.stderr)
        return 1

    text = verdict_path.read_text()
    rtype, facet, lens = parse_head(text)

    # ---- build / fill / ship: no pair to reveal, but the round still has to
    # ---- say what it did and whether the gates held.
    if not key_path.is_file():
        did = DID_RE.search(text)
        gates = GATES_RE.search(text)
        if not did:
            print("error: verdict.md has no `DID:` line. Say in one sentence what this round\n"
                  "built. A round that cannot state that did not happen.", file=sys.stderr)
            return 1
        if not gates:
            print("error: verdict.md has no `GATES:` line. Record whether the free gates passed\n"
                  "— a build nobody checked is a build nobody can trust at round 40.",
                  file=sys.stderr)
            return 1
        did_text, gates_text = did.group(1).strip(), gates.group(1).strip()
        failed = bool(re.match(r"\s*(fail|no|broken)", gates_text, re.I))
        # `GATES: fail — <name>` names the culprit; next.py counts repeats of the
        # same name towards quarantine.
        gate_m = re.search(r"(?:fail\w*|no|broken)\s*[—:-]\s*(.+)", gates_text, re.I)
        failed_gate = gate_m.group(1).strip() if failed and gate_m else ""

        autocommit = "AUTOCOMMIT: no" not in (run_dir / "STATE.md").read_text(errors="replace") \
            if (run_dir / "STATE.md").is_file() else True
        snap = snapshot(rd, f"round {rd.name} — {rtype}"
                            + (f" {facet}" if facet else "") + f" — {did_text[:60]}", autocommit)

        (rd / "outcome.json").write_text(json.dumps({
            "round": rd.name, "type": rtype if rtype != "POLISH" else "BUILD",
            "ts": datetime.now().isoformat(timespec="seconds"),
            "facet": facet, "lens": "", "winner": "", "gap": "",
            "did": did_text, "gates": gates_text, "gates_failed": failed,
            "failed_gate": failed_gate, **snap,
        }, indent=2, ensure_ascii=False) + "\n")

        result = "GATES FAILED" if failed else "done"
        state = append_ledger(run_dir, f"| {rd.name} | {rtype} | {facet or '-'} | - | "
                                       f"{result} | {cell(did_text)} |\n")
        print(f"{rtype} round {rd.name} logged — {result}")
        print(f"ledger updated: {state}")
        if failed:
            print("Gates failed. Fixing that outranks whatever the next round was going to be:\n"
                  "a gate that stops passing is a regression, and regressions compound.")
        return 0

    # ---- polish: commit-then-reveal ----------------------------------------
    win = WINNER_RE.search(text)
    gap = GAP_RE.search(text)
    if not win:
        print("error: verdict.md has no committed pick. Add a line `WINNER: A` (or B, or TIE)\n"
              "before revealing.", file=sys.stderr)
        return 1
    if not gap:
        print("error: verdict.md names no gap. Add a line `GAP: <the single biggest gap>` —\n"
              "exactly one, so the next round has exactly one target. A list becomes a shotgun\n"
              "patch and then nothing tells you which change moved the needle.", file=sys.stderr)
        return 1

    picked = win.group(1).upper()
    gap_text = gap.group(1).strip()
    key = json.loads(key_path.read_text())

    if picked == "TIE":
        winner, outcome, note = "TIE", "TIE", "Neither side clearly won this lens."
    else:
        role = key.get(picked, "?")
        winner = "BAR" if role == "reference" else "OURS"
        outcome = "BAR WINS" if winner == "BAR" else "OURS WINS"
        note = f"You picked {picked}, which was the {role}."

    with verdict_path.open("a") as fh:
        fh.write(f"\n## Reveal\n\n"
                 f"- A = {key.get('A', '?')}\n"
                 f"- B = {key.get('B', '?')}\n"
                 f"- picked: {picked} → **{outcome}**\n"
                 f"- {note}\n")
        if winner == "OURS":
            fh.write("- Self-recognition check: you built this candidate, so you may have\n"
                     "  recognised it rather than judged it. Re-read the rubric line you scored\n"
                     "  on — if your stated reason does not survive that re-read, treat this as\n"
                     "  BAR WINS and keep going.\n")

    autocommit = "AUTOCOMMIT: no" not in (run_dir / "STATE.md").read_text(errors="replace") \
        if (run_dir / "STATE.md").is_file() else True
    snap = snapshot(rd, f"round {rd.name} — POLISH"
                        + (f" {facet}" if facet else "") + f" — {gap_text[:60]}", autocommit)

    (rd / "outcome.json").write_text(json.dumps({
        "round": rd.name, "type": "POLISH", "facet": facet, "lens": lens,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "picked": picked, "winner": winner, "outcome": outcome, "gap": gap_text,
        "A": key.get("A"), "B": key.get("B"), **snap,
    }, indent=2, ensure_ascii=False) + "\n")

    state = append_ledger(run_dir, f"| {rd.name} | POLISH | {facet or '-'} | {lens or '-'} | "
                                   f"{outcome} | {cell(gap_text)} |\n")

    print(f"{outcome} — {note}")
    print(f"gap to close this round: {gap_text}")
    print(f"ledger updated: {state}")
    if winner == "OURS":
        print("A single win is noise. The facet counts as won only when ours takes every lens\n"
              "across one full rotation — next.py tracks that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
