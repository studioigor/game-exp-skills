#!/usr/bin/env python3
"""Count what exists against what the scope contract promised.

This is the script that stops a "clone of Need for Speed" from reporting done
with three tracks and a menu. Every contract line carries a `count:` command; this
runs them, compares the number against the target, and prints the standing.

It also keeps a baseline of the contract's line names, written the first time it
runs successfully. If a line later disappears, it says so. Deleting a contract
line is the quietest way to lower a standard — it leaves nothing behind to notice.

Usage:
  contract.py .gamemaker/<slug> [--json]

Exit status is 0 when every line is met or explicitly BLOCKED, 1 otherwise, so
it works directly as a ladder gate check.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

GATE = re.compile(r"^-\s+\[( |x|X)\]\s+(.*)$")
PLACEHOLDER = re.compile(r"<[^<>\n]{2,}>")
BASELINE = "contract-baseline.json"


def parse(text: str) -> list[dict]:
    """One dict per contract line: name, target, unit, count command, state."""
    lines = []
    body = text.split("## Contract", 1)[-1] if "## Contract" in text else text
    for raw in body.splitlines():
        g = GATE.match(raw.strip())
        if not g:
            continue
        t = g.group(2).strip()
        cm = re.search(r"—\s*count:\s*(.*)$", t)
        head = t[: cm.start()].strip() if cm else t
        nm = re.match(r"(.+?):\s*(\S+)\s*(.*)$", head)
        lines.append({
            "raw": t,
            "name": (nm.group(1) if nm else head).strip(),
            "target": (nm.group(2) if nm else "").strip(),
            "unit": (nm.group(3) if nm else "").strip(),
            "count": cm.group(1).strip() if cm else "",
            "ticked": g.group(1).lower() == "x",
            "blocked": "BLOCKED:" in t,
        })
    return lines


def run_count(cmd: str, cwd: Path) -> tuple[int | None, str]:
    """Run a `count:` command and take the last number it prints."""
    if not cmd or cmd.startswith("manual:") or PLACEHOLDER.search(cmd):
        return None, "not counted"
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True,
                           text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None, "timed out"
    if p.returncode != 0:
        return None, f"exit {p.returncode}: {(p.stderr or p.stdout).strip()[:60]}"
    nums = re.findall(r"-?\d+", p.stdout)
    if not nums:
        return None, f"printed no number: {p.stdout.strip()[:60]}"
    return int(nums[-1]), ""


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print("usage: contract.py .gamemaker/<slug> [--json]", file=sys.stderr)
        return 2
    run = Path(args[0])
    src = run / "CONTRACT.md"
    if not src.is_file():
        print(f"error: no CONTRACT.md in {run}", file=sys.stderr)
        return 2

    # Counting happens from the project root, not the run dir — the commands are
    # written against the game's own layout.
    cwd = run.parent.parent if run.parent.name == ".gamemaker" else Path.cwd()

    lines = parse(src.read_text(errors="replace"))
    real = [l for l in lines if not PLACEHOLDER.search(l["name"])]

    results = []
    for l in real:
        have, note = run_count(l["count"], cwd)
        try:
            target = int(re.sub(r"\D", "", l["target"]) or 0)
        except ValueError:
            target = 0
        if l["blocked"]:
            status = "BLOCKED"
        elif have is None:
            status = "UNCOUNTED"
        elif target and have >= target:
            status = "MET"
        else:
            status = "SHORT"
        results.append({**l, "have": have, "target_n": target,
                        "status": status, "note": note})

    # Tamper check: a contract line that used to exist and no longer does.
    bl = run / BASELINE
    known = json.loads(bl.read_text()).get("names", []) if bl.is_file() else []
    names = [l["name"] for l in real]
    gone = [k for k in known if k not in names]
    if real and not gone:
        bl.write_text(json.dumps({"names": sorted(set(known) | set(names))}, indent=2))

    if as_json:
        print(json.dumps({"lines": results, "deleted": gone}, indent=2, ensure_ascii=False))
    else:
        print(f"contract — {run.name}")
        if not real:
            print("  no real contract lines yet — CONTRACT.md is still the template.")
            return 1
        width = max(len(l["name"]) for l in real)
        for r in results:
            have = "?" if r["have"] is None else r["have"]
            mark = {"MET": "✓", "SHORT": "·", "BLOCKED": "▪", "UNCOUNTED": "?"}[r["status"]]
            tail = f"   {r['note']}" if r["note"] else ""
            print(f"  {mark} {r['name']:<{width}}  {have}/{r['target_n']} {r['unit']}"
                  f"   {r['status']}{tail}")
            if r["status"] == "MET" and not r["ticked"]:
                print(f"      → target reached; tick this line in CONTRACT.md")
            if r["status"] == "SHORT" and r["ticked"]:
                print(f"      → ticked but short. Ticking a line that has not reached its "
                      f"target is the same move as deleting it.")
        met = sum(1 for r in results if r["status"] in ("MET", "BLOCKED"))
        print(f"\n  {met}/{len(results)} lines met or blocked")
        if gone:
            print(f"\n  ! {len(gone)} contract line(s) present at baseline are now missing:")
            for g in gone:
                print(f"      {g}")
            print("    Contract lines are never deleted, only ticked or marked BLOCKED.")
            print("    Restore them, or mark them BLOCKED with a reason.")

    open_lines = [r for r in results if r["status"] in ("SHORT", "UNCOUNTED")]
    return 1 if (open_lines or gone) else 0


if __name__ == "__main__":
    sys.exit(main())
