#!/usr/bin/env python3
"""Say what this firing of a gamemaker run should do, and nothing else.

Reads the run off disk, works out which rung of the ladder it is on, and prints
one unit of work: the stage, what is still blocking it, the round type, the
facet, the capture command, the contract standing, the budget, and any warning
worth acting on.

Everything it needs is on disk, so a cleared context costs nothing: this is what
makes a night run resumable and each firing independent.

It deliberately refuses to hand out work from a later stage. A gauntlet-style
polish round applied to a game that is 40% built produces a beautifully polished
40%, and the missing 60% never surfaces as a gap because no round is ever pointed
at it.

Usage:
  next.py .gamemaker/<slug>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STAGES = ["BRIEF", "DESIGN", "HARNESS", "SLICE", "SYSTEMS", "CONTENT", "POLISH", "SHIP"]

PURPOSE = {
    0: "pin the ambition and commit to a scope contract with real numbers",
    1: "decide what this game is — pillars, the loop at three scales, systems, economy",
    2: "choose a stack whose capture runs without a human, and prove that it does",
    3: "build the whole thing end to end, ugly, and answer the validation question",
    4: "ship every mvp system in DESIGN.md, with a check each",
    5: "fill the scope contract — the volume that separates a game from a demo",
    6: "beat the bar facet by facet, one gap per round, lenses rotating",
    7: "make it shippable: soak it, strip the placeholders, meet the platform",
}

ROUND_TYPE = {3: "BUILD", 4: "BUILD", 5: "FILL", 6: "POLISH", 7: "SHIP"}

# What a round of each type means, printed so a fresh context does not have to
# re-derive it from the skill body.
TYPE_NOTE = {
    "BUILD": ("the gap is a missing capability, not a quality shortfall. No critic and no "
              "blind pair — the gates decide. Build the one thing, run the gates, log it."),
    "FILL": ("the gap is a missing count. Build the content unit, then re-run contract.py. "
             "Not judged, counted — this is the cheapest round type and most of the volume."),
    "POLISH": ("the classic round: free gates, capture, blind A/B against this facet's bar, "
               "exactly one gap, then close it. Everything else noticed goes to open_gaps.md."),
    "SHIP": ("the gap is a release blocker. Same shape as BUILD, but the gates come from "
             "stage 7 and from references/ship.md."),
}

PLACEHOLDER = re.compile(r"<[^<>\n]{2,}>")
STAGE_HDR = re.compile(r"^##\s+Stage\s+(\d+)\s+—\s+(\S+)", re.M)
GATE = re.compile(r"^-\s+\[( |x|X)\]\s+(.*)$")
FIELD = re.compile(r"^([A-Z][A-Z ]+):[ \t]*(.*)$", re.M)


def read(p: Path) -> str:
    return p.read_text(errors="replace") if p.is_file() else ""


def strip_code(text: str) -> str:
    """Drop inline code spans and indented blocks.

    Angle brackets inside them are documentation — the syntax examples in every
    template — not things waiting to be filled in. Without this the templates
    could never come clean and the ladder would never open.
    """
    out = []
    for line in text.splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            continue
        out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def placeholders(text: str) -> list[str]:
    return PLACEHOLDER.findall(strip_code(text))


def field(text: str, name: str) -> str:
    for m in FIELD.finditer(text):
        if m.group(1).strip() == name:
            return m.group(2).strip()
    return ""


def is_blocked(s: str) -> bool:
    return "BLOCKED:" in s


def parse_ladder(text: str) -> list[dict]:
    """Split LADDER.md into stages with their owned files and their gates."""
    stages: list[dict] = []
    marks = list(STAGE_HDR.finditer(text))
    for i, m in enumerate(marks):
        body = text[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(text)]
        files: list[str] = []
        fm = re.search(r"^files:\s*(.*)$", body, re.M)
        if fm and "(none)" not in fm.group(1):
            files = [f.strip() for f in fm.group(1).split(",") if f.strip()]
        gates = []
        for line in body.splitlines():
            g = GATE.match(line.strip())
            if g:
                gates.append({"done": g.group(1).lower() == "x", "text": g.group(2).strip()})
        stages.append({"num": int(m.group(1)), "name": m.group(2), "files": files, "gates": gates})
    return stages


def check_of(gate_text: str) -> str:
    m = re.search(r"—\s*check:\s*(.*)$", gate_text)
    return m.group(1).strip() if m else ""


def section(text: str, heading: str) -> str:
    """The body under `## heading`, up to the next `##`.

    Every one of these files carries guidance prose above its data, and the
    guidance is written in the same bullet syntax as the data. Without scoping,
    the explanation of what a good pillar looks like parses as the pillars.
    """
    m = re.search(rf"^##\s+{re.escape(heading)}\s*$", text, re.M | re.I)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def parse_named(text: str) -> list[tuple[str, str]]:
    """`- **name** — rest` lines, which is how every table in this run is written."""
    out = []
    for line in text.splitlines():
        m = re.match(r"^-\s+\*\*(.+?)\*\*\s*—\s*(.*)$", line.strip())
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def sub_field(rest: str, name: str) -> str:
    """Pull `name:` out of a `key: value — key: value` tail. `capture:` runs to end."""
    m = re.search(rf"\b{name}:\s*(.*?)(?:\s+—\s+\w+:|$)", rest)
    return m.group(1).strip() if m else ""


def parse_bars(text: str) -> dict[str, dict]:
    bars = {}
    for name, rest in parse_named(text):
        if " " in name:  # the prose bullets above the table
            continue
        bars[name.lower()] = {
            "bar": sub_field(rest, "bar"),
            "ref": sub_field(rest, "ref"),
            "capture": sub_field(rest, "capture"),
        }
    return bars


def parse_rubric(text: str) -> dict[str, list[str]]:
    lenses: dict[str, list[str]] = {}
    for name, _q in parse_named(text):
        if "/" not in name:
            continue
        facet, lens = name.split("/", 1)
        lenses.setdefault(facet.strip().lower(), []).append(lens.strip())
    return lenses


def parse_backlog(text: str) -> list[dict]:
    items = []
    for line in text.splitlines():
        # Indented lines are the syntax example, not work. Without this the
        # template's own example line gets handed out as round 1's unit.
        if line.startswith("    ") or line.startswith("\t"):
            continue
        g = GATE.match(line.strip())
        if not g:
            continue
        body = g.group(2)
        if PLACEHOLDER.search(body):
            continue
        sm = re.search(r"stage:\s*(\d+)", body)
        fm = re.search(r"facet:\s*([a-z]+)", body)
        what = re.sub(r"^stage:\s*\d+\s*—\s*", "", body)
        what = re.sub(r"^facet:\s*[a-z]+\s*—\s*", "", what)
        items.append({"done": g.group(1).lower() == "x",
                      "stage": int(sm.group(1)) if sm else None,
                      "facet": fm.group(1) if fm else "",
                      "text": what.strip()})
    return items


def parse_contract(text: str) -> list[dict]:
    lines = []
    body = text.split("## Contract", 1)[-1] if "## Contract" in text else text
    for line in body.splitlines():
        g = GATE.match(line.strip())
        if g:
            lines.append({"done": g.group(1).lower() == "x", "text": g.group(2).strip()})
    return lines


def load_rounds(run: Path) -> list[dict]:
    out = []
    for d in sorted((run / "rounds").glob("*")):
        f = d / "outcome.json"
        if f.is_file():
            try:
                o = json.loads(f.read_text())
                o["dir"] = d.name
                out.append(o)
            except json.JSONDecodeError:
                pass
    return out


def least_recent(options: list[str], history: list[str]) -> str:
    """The option unused longest — so a skipped round repairs the rotation."""
    for o in options:
        if o not in history:
            return o
    return min(options, key=lambda o: len(history) - 1 - history[::-1].index(o))


def next_round_num(run: Path) -> int:
    ns = [int(d.name) for d in (run / "rounds").glob("*") if d.name.isdigit()]
    return (max(ns) + 1) if ns else 1


def facet_won(rounds: list[dict], facet: str, lens_count: int) -> bool:
    """A facet is won when it takes every lens across one clean rotation.

    A single win is noise; a full rotation is a result.
    """
    got = [r for r in rounds if r.get("facet") == facet and r.get("type") == "POLISH"]
    if lens_count == 0 or len(got) < lens_count:
        return False
    tail = got[-lens_count:]
    return (all(r.get("winner") == "OURS" for r in tail)
            and len({r.get("lens") for r in tail}) == lens_count)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: next.py .gamemaker/<slug>", file=sys.stderr)
        return 2
    run = Path(sys.argv[1])
    if not run.is_dir():
        print(f"error: no such run: {run}", file=sys.stderr)
        return 2

    here = Path(__file__).resolve().parent
    state = read(run / "STATE.md")
    ladder = parse_ladder(read(run / "LADDER.md"))
    if not ladder:
        print("error: LADDER.md is missing or its stage headers do not match "
              "`## Stage N — NAME`. Re-run init.py.", file=sys.stderr)
        return 2

    print(f"gamemaker — {run.name}")
    print(f"ambition: {field(state, 'AMBITION') or '?'}  ·  "
          f"reference: {field(state, 'REFERENCE') or '?'}  ·  "
          f"scale: {field(state, 'SCALE') or '?'}")

    pillars = [n for n, _ in parse_named(section(read(run / "PILLARS.md"), "Pillars"))
               if not PLACEHOLDER.fullmatch(n)]
    if pillars:
        print(f"pillars: {' · '.join(pillars)}")

    # --- which rung are we on -------------------------------------------------
    current = None
    for st in ladder:
        st["file_gaps"] = []
        for f in st["files"]:
            ph = placeholders(read(run / f))
            if not (run / f).is_file():
                st["file_gaps"].append((f, ["file missing"]))
            elif ph:
                st["file_gaps"].append((f, ph))
        st["open"] = [g for g in st["gates"] if not g["done"] and not is_blocked(g["text"])]
        st["blocked"] = [g for g in st["gates"] if is_blocked(g["text"])]
        st["bad_ticks"] = [g for g in st["gates"]
                           if g["done"] and PLACEHOLDER.search(check_of(g["text"]))]
        if current is None and (st["file_gaps"] or st["open"]):
            current = st

    if current is None:
        print("\nALL STAGES CLOSED — the ladder is finished.")
        blocked = [(s["num"], g["text"]) for s in ladder for g in s["blocked"]]
        contract = parse_contract(read(run / "CONTRACT.md"))
        open_c = [c for c in contract if not c["done"] and not is_blocked(c["text"])]
        if open_c:
            print(f"\nBut {len(open_c)} contract line(s) are still open. The run does not "
                  f"report done while the contract is open — reopen stage 5.")
            for c in open_c[:8]:
                print(f"    - {c['text']}")
            return 0
        print("\nReport: rounds run, what each facet still loses to the bar (open_gaps.md),")
        print("and — first and plainly — every gate and contract line that shipped BLOCKED:")
        for num, t in blocked:
            print(f"    stage {num}: {t}")
        for c in contract:
            if is_blocked(c["text"]):
                print(f"    contract: {c['text']}")
        return 0

    n = current["num"]
    closed = [s["num"] for s in ladder if s["num"] < n]
    print(f"\nSTAGE {n} — {current['name']}"
          + (f"   (stages {min(closed)}–{max(closed)} closed)" if closed else ""))
    print(f"  {PURPOSE.get(n, '')}")

    for st in ladder:
        for g in st["bad_ticks"]:
            print(f"\n  ! stage {st['num']}: a gate is ticked but its check is still a "
                  f"placeholder — {g['text']}")
            print("    Untick it or write the real check. Every later stage assumes this one is true.")

    # --- setup stages: the work is to finish the stage, not to run a round ----
    if n <= 2:
        print(f"\nNOT READY — stage {n} is where the work is. Still open:")
        for f, ph in current["file_gaps"]:
            shown = ", ".join(p[:58] for p in ph[:3])
            more = f" (+{len(ph) - 3} more)" if len(ph) > 3 else ""
            print(f"    {f} — {len(ph)} placeholder(s): {shown}{more}")
        for g in current["open"]:
            print(f"    [ ] {g['text']}")
        if n == 2:
            proven = field(read(run / "HARNESS.md"), "CAPTURE PROVEN").lower()
            print("\n  The capture is the highest-leverage thing in the whole run: without it a")
            print("  critic grades a description of the game, and descriptions always pass.")
            if proven != "yes":
                print("  HARNESS.md says the capture is not proven yet. Prove it mechanically:")
                print(f"      python3 {here / 'preflight.py'} {run}")
                print("  It runs the session twice, checks determinism, and flips the flag itself.")
                print("  If this stack cannot pass it, say so plainly and switch to user-paced")
                print("  rounds; a firing spent failing the same gate is the most expensive way")
                print("  to find that out.")
            print("  See references/harness.md.")
        if n == 1:
            print("\n  See references/design.md (genre blueprints, the holism checklist) and")
            print("  references/art.md — ART.md is a stage 1 output, chosen before any code,")
            print("  because an identity cannot be retrofitted by polish rounds.")
        print(f"\nNEXT: close stage {n}. Do not start building past it.")
        return 0

    # --- round stages ---------------------------------------------------------
    rounds = load_rounds(run)
    rnum = next_round_num(run)
    rtype = ROUND_TYPE.get(n, "BUILD")
    bars = parse_bars(read(run / "BARS.md"))
    backlog = parse_backlog(read(run / "BACKLOG.md"))
    contract = parse_contract(read(run / "CONTRACT.md"))

    # A stalled gap parks its facet: the same gap 3 rounds running means the fix
    # is not landing, and a fourth identical round is spend, not persistence.
    gaps3 = [r.get("gap", "").strip().lower() for r in rounds[-3:] if r.get("gap")]
    stalled_facet = rounds[-1].get("facet", "") \
        if (len(gaps3) == 3 and len(set(gaps3)) == 1) else ""

    facet, lens, unit = "", "", ""

    if rtype == "POLISH":
        rubric = parse_rubric(read(run / "RUBRIC.md"))
        usable = [f for f in rubric if f in bars and bars[f]["capture"]
                  and not PLACEHOLDER.search(bars[f]["capture"])]
        if not rubric:
            print("\nNOT READY — RUBRIC.md has no lenses in `- **facet/lens** — question` form.")
            print("  Polish is the one stage that needs a frozen rubric: written after seeing the")
            print("  output, a rubric is shaped by the output. Re-run init.py to get the starter")
            print("  set, then adapt every line to the bars in BARS.md.")
            return 0
        if not usable:
            print("\nNOT READY — no facet in RUBRIC.md has a usable capture in BARS.md.")
            print(f"  rubric facets: {', '.join(sorted(rubric))}")
            print(f"  facets with a real capture: {', '.join(sorted(f for f in bars if bars[f]['capture'] and not PLACEHOLDER.search(bars[f]['capture']))) or 'none'}")
            print("  Polish cannot start until at least one facet can be captured and compared:")
            print("  a critic with nothing to look at grades a description, and descriptions pass.")
            return 0
        won = [f for f in usable if facet_won(rounds, f, len(rubric[f]))]
        left = [f for f in usable if f not in won]
        if stalled_facet and stalled_facet in left and len(left) > 1:
            left = [f for f in left if f != stalled_facet]
            print(f"  facet '{stalled_facet}' is parked for this pick — its gap has stalled "
                  f"3 rounds running (see warning below).")
        if not left:
            print("\nSTOP CONDITION MET — every facet has taken a clean lens rotation against "
                  "its bar.")
            print("  Tick stage 6's gates and move to SHIP. A run that reports total victory is")
            print("  usually a run whose bar was too low — check open_gaps.md before you agree.")
            return 0
        facet = least_recent(left, [r.get("facet", "") for r in rounds if r.get("type") == "POLISH"])
        lens = least_recent(rubric[facet],
                            [r.get("lens", "") for r in rounds if r.get("facet") == facet])
        unit = f"{facet} under the {lens} lens"
        if won:
            print(f"  facets already won: {', '.join(won)}")
    elif rtype == "FILL":
        open_c = [c for c in contract if not c["done"] and not is_blocked(c["text"])]
        if not open_c:
            print("\nContract is closed. Tick stage 5's gates and move on.")
            return 0
        facet = "content"
        unit = open_c[0]["text"]
    else:
        todo = [b for b in backlog if not b["done"] and (b["stage"] is None or b["stage"] == n)]
        # Architecture debt is paid before features, wherever the lines sit in
        # the file — a feature built on a bad seam is built twice.
        todo.sort(key=lambda b: not b["text"].lower().startswith("refactor:"))
        if not todo:
            print(f"\nBACKLOG EMPTY for stage {n}, but the stage is not closed. That is the")
            print("  signal to decompose the stage's remaining gates into backlog items —")
            print("  not to move on. Still open:")
            for g in current["open"]:
                print(f"    [ ] {g['text']}")
            if n == 4:
                systems = [(s, r) for s, r in parse_named(section(read(run / "DESIGN.md"), "Systems"))
                           if "tier: mvp" in r and not PLACEHOLDER.search(s)]
                if systems:
                    print("\n  Stage 4 is the mvp systems list in DESIGN.md. Decompose from these:")
                    for s, r in systems:
                        print(f"    - {s} — {sub_field(r, 'check') or 'no check written'}")
            return 0
        facet = todo[0]["facet"]
        unit = todo[0]["text"]

    print(f"\nROUND {rnum:02d} — type: {rtype}" + (f" — facet: {facet}" if facet else ""))
    print(f"  {TYPE_NOTE[rtype]}")
    print(f"\nunit: {unit}")
    if unit.lower().startswith("refactor:"):
        print("  a refactor unit is handed out before features on purpose: architecture debt")
        print("  is paid first (references/code.md). One seam, gates green at the end, and add")
        print("  the check that keeps the seam clean.")

    cap = bars.get(facet, {}).get("capture", "")
    if cap and not PLACEHOLDER.search(cap):
        print(f"capture: {cap}")
    bar = bars.get(facet, {}).get("bar", "")
    if bar and not PLACEHOLDER.search(bar):
        print(f"bar: {bar}")

    gate_cmds = [check_of(g["text"]) for g in current["gates"]]
    gate_cmds = [c for c in gate_cmds if c and not c.lower().startswith("manual")
                 and not PLACEHOLDER.search(c)]
    if gate_cmds:
        print("\nfree gates — run these before anything else; broken output is fixed, not judged:")
        for c in gate_cmds:
            print(f"    {c}")

    rdir = run / "rounds" / f"{rnum:02d}"
    if rtype == "POLISH":
        ref = bars.get(facet, {}).get("ref", "")
        print(f"\nblind pair:\n    python3 {here / 'ab.py'} --round {rdir} \\\n"
              f"      --ref {run / ref if ref and ref != 'none' else '<this facet reference>'} "
              f"--cand <this round's capture output>")
        print("    Do not read key.json, and do not `ls -l` the pair — file sizes are a tell.")

    met = sum(1 for c in contract if c["done"])
    blocked_c = sum(1 for c in contract if is_blocked(c["text"]))
    if contract:
        print(f"\ncontract: {met}/{len(contract)} met"
              + (f", {blocked_c} blocked" if blocked_c else "")
              + (f"   (verify: python3 {here / 'contract.py'} {run})" if n >= 5 else ""))

    budget = re.search(r"Budget:\s*stop after round\s*(\d+)", state)
    if budget:
        cap_n = int(budget.group(1))
        print(f"budget: round {rnum} of {cap_n}")
        if rnum > cap_n:
            print("  BUDGET SPENT — stop and report. Do not quietly extend it.")

    print(f"\nverdict → {rdir / 'verdict.md'}")
    print(f"log     → python3 {here / 'reveal.py'} {rdir}")

    # --- warnings -------------------------------------------------------------
    warn: list[str] = []

    if stalled_facet:
        warn.append(f"STALL — the same gap has come back 3 rounds running: {gaps3[0][:70]}\n"
                    f"    The facet ('{stalled_facet}') is parked for this pick. Move the gap to\n"
                    "    open_gaps.md prefixed `STALLED:`, rewrite it as \"the bar has X where\n"
                    "    ours has Y\", and come back to it next rotation. Grinding is not\n"
                    "    persistence.")

    noop3 = [r.get("src_changed") for r in rounds[-3:]]
    if len(noop3) == 3 and all(v is False for v in noop3):
        warn.append("NO-OP STREAK — the last 3 rounds changed no game file: only harness, tests,\n"
                    "    tooling or docs moved. The run is polishing its own scaffolding. A round's\n"
                    "    unit changes something the player sees or plays — take the next backlog\n"
                    "    or contract unit and build it.")

    fg3 = [r.get("failed_gate", "") for r in rounds[-3:]]
    if len(fg3) == 3 and fg3[0] and len(set(fg3)) == 1:
        warn.append(f"GATE QUARANTINE — '{fg3[0]}' has failed 3 rounds running. Do not spend a\n"
                    "    fourth: mark that gate `BLOCKED: quarantined round "
                    f"{rnum:02d} — <why>` in LADDER.md,\n"
                    "    add a line to open_gaps.md, and keep building. It ships in the final\n"
                    "    report as BLOCKED — visible, not buried under a night of retries.")

    if rnum > 1 and rnum % 15 == 1 and n >= 4:
        warn.append("ARCH CHECK DUE — run the audit in references/code.md against the current\n"
                    "    code: layout drift, un-seeded randomness, tuning numbers leaking into\n"
                    "    systems, a growing god object. Findings become `refactor:` lines in\n"
                    "    BACKLOG.md, and refactor lines are handed out first.")

    if rnum > 1 and rnum % 12 == 1 and n >= 3:
        warn.append("DESIGN CHECK DUE — run the holism checklist in references/design.md and put\n"
                    "    what it finds into open_gaps.md. Competing progression loops, an\n"
                    "    overloaded attention budget and a dominant strategy are invisible to\n"
                    "    every lens in the rubric, because no single capture shows them.")

    if rnum > 1 and rnum % 25 == 1 and n >= 4:
        warn.append("SOAK DUE — run the long session instead of the short one this round. Leaks,\n"
                    "    frame-time drift, state accumulation and content exhaustion only appear\n"
                    "    after sustained play, and none of them show up in a 30-second strip.")

    proven = field(read(run / "HARNESS.md"), "CAPTURE PROVEN").lower()
    if proven != "yes":
        warn.append("HARNESS NOT PROVEN — HARNESS.md still says the capture has not been proven\n"
                    "    to run without a human. Unattended rounds past this point are a guess.\n"
                    f"    Prove it: python3 {here / 'preflight.py'} {run}")

    if warn:
        print()
        for w in warn:
            print(f"  {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
