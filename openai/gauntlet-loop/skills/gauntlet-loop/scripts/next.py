#!/usr/bin/env python3
"""Work out what the next Gauntlet round should be — deterministically.

Reads the run on disk (BAR.md, RUBRIC.md, PIECES.md, STATE.md, rounds/*) and
prints the next round number, which lens and piece are up, the capture command
to use, a ready-to-paste ab.py invocation, the budget standing, and whether any
stop condition has actually been met.

This exists to keep an unattended round cheap. Deriving "which lens is next"
from four files costs model tokens every round and can drift; here it is a
function of the ledger, so a Goal continuation after context compaction can spend
its whole budget on the work instead of on re-orienting.

It also checks the two things a builder is worst at judging about its own run:
whether the win streak really covers a full rotation, and whether the last few
rounds have been chasing the same gap without moving it.

Usage:
  next.py .gauntlet/<slug> [--json] [--rotate lens|piece]
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

BULLET_RE = re.compile(r"^[ \t]*[-*][ \t]+\*\*(.+?)\*\*[ \t]*(?:[—\-–:][ \t]*(.*))?$", re.M)
H3_RE = re.compile(r"^###[ \t]+(.+?)[ \t]*$", re.M)
CAPTURE_RE = re.compile(r"capture:[ \t]*(.+?)[ \t]*$", re.I)
FACET_RE = re.compile(r"facet:[ \t]*([a-zA-Zа-яА-Я]+)", re.I)
GATE_RE = re.compile(r"^[ \t]*[-*][ \t]*\[([ xX])\][ \t]*(.+?)[ \t]*$", re.M)
BUDGET_RE = re.compile(r"(?:^[ \t]*(?:\*\*)?BUDGET(?:\*\*)?:[ \t]*(\d+)"
                       r"|Budget:[^\n]*?stop after round[ \t]+(\d+))", re.I | re.M)
FIELD_RE = r"^[ \t]*(?:\*\*)?{}(?:\*\*)?:[ \t]*(.+?)[ \t]*$"

SCRIPTS = Path(__file__).resolve().parent

# Kinds whose deliverable is a whole product. These carry DELIVERABLE.md and get the
# two extra checks below, both aimed at one failure: a run asked for a *game* that
# spends every round on how the game looks.
PRODUCT_KINDS = {"game", "product"}
SURFACE_FACETS = {"visual", "ui", "ux", "art"}


def field(text: str, name: str) -> str:
    m = re.search(FIELD_RE.format(name), text, re.I | re.M)
    return m.group(1).strip() if m else ""


def read(p: Path) -> str:
    return p.read_text(errors="replace") if p.is_file() else ""


def named_items(text: str) -> list[tuple[str, str]]:
    """Parse `- **name** — detail` bullets, falling back to `### name` headings."""
    items = [(m.group(1).strip(), (m.group(2) or "").strip()) for m in BULLET_RE.finditer(text)]
    if items:
        return items
    return [(m.group(1).strip(), "") for m in H3_RE.finditer(text)]


def pad_for(n: int) -> int:
    return max(2, len(str(n)))


def is_placeholder(s: str) -> bool:
    """True for text still carrying init.py's scaffolding, e.g. `<piece name>` or `<TODO: ...>`.

    Worth checking mechanically: a run that starts on the template looks exactly
    like a real run in every file listing, and the mistake only becomes visible
    after a night of rounds spent grading a placeholder.
    """
    s = s.strip()
    return bool(re.search(r"<[^>]*>", s)) or s.upper().startswith("TODO")


def render_capture(template: str, artifact: Path, round_dir: Path, round_name: str) -> str:
    """Resolve a stable capture template for the current round."""
    return (template
            .replace("{artifact}", shlex.quote(str(artifact)))
            .replace("{round_dir}", shlex.quote(str(round_dir)))
            .replace("{round}", round_name))


def normalise_gap(s: str) -> str:
    return re.sub(r"[^a-z0-9а-яё ]+", " ", s.lower()).split().__str__()


def load_rounds(run: Path) -> list[dict]:
    out = []
    rounds_dir = run / "rounds"
    if not rounds_dir.is_dir():
        return out
    for rd in sorted((p for p in rounds_dir.glob("*") if p.is_dir()), key=lambda p: p.name):
        oc = rd / "outcome.json"
        data = json.loads(read(oc)) if oc.is_file() else {}
        out.append({
            "dir": rd,
            "name": rd.name,
            "outcome": data.get("outcome", "pending"),
            "lens": data.get("lens", "-"),
            "piece": data.get("piece", "-"),
            "gap": data.get("gap", ""),
            "settled": bool(data),
        })
    return out


def least_recent(options: list[str], history: list[str]) -> str:
    """The option unused for longest — never used at all beats used long ago.

    Rotating off the round counter breaks the moment a round is skipped, redone,
    or added by hand: the counter says lens 3 while the ledger shows lens 3 ran
    twice and lens 5 never did. Deriving it from what actually happened means a
    run repairs its own rotation instead of quietly grading the same lens twice.
    """
    lowered = [h.strip().lower() for h in history]
    def last_seen(opt: str) -> int:
        key = opt.strip().lower()
        for i in range(len(lowered) - 1, -1, -1):
            if lowered[i] == key:
                return i
        return -1
    return min(options, key=lambda o: (last_seen(o), options.index(o)))


def pick_piece(pieces: list[tuple[str, str]], rounds: list[dict], lenses: list[str],
               mode: str) -> tuple[str, str]:
    """Which piece the next round works on.

    Default (`lens`): stay on a piece until its lens rotation is complete, then
    move on — that way "ours wins across a full rotation" means something about a
    piece rather than about a shuffle. `piece` mode alternates every round, which
    suits runs where the pieces interact and drifting apart is the bigger risk.
    """
    settled = [r for r in rounds if r["settled"]]
    names = [p[0] for p in pieces]
    if not settled:
        return pieces[0]
    current = settled[-1]["piece"].strip()
    idx = next((i for i, n in enumerate(names) if n.strip().lower() == current.lower()), 0)
    if mode == "piece":
        return pieces[(idx + 1) % len(pieces)]
    tail = [r for r in settled[-len(lenses):] if r["piece"].strip().lower() == current.lower()]
    covered = {r["lens"].strip().lower() for r in tail}
    if len(tail) >= len(lenses) and covered == {l.strip().lower() for l in lenses}:
        return pieces[(idx + 1) % len(pieces)]
    return pieces[idx]


def clean_rotation(rounds: list[dict], lenses: list[str]) -> tuple[bool, str]:
    """A run stops on a clean rotation, not on a lucky round.

    The last len(lenses) settled rounds must cover every lens once and every one
    of them must have gone to us. One win is noise; a rotation is a result.
    """
    settled = [r for r in rounds if r["settled"]]
    if not lenses or len(settled) < len(lenses):
        return False, f"needs {len(lenses)} settled rounds covering every lens; have {len(settled)}"
    tail = settled[-len(lenses):]
    covered = {r["lens"].strip().lower() for r in tail}
    want = {l.strip().lower() for l in lenses}
    wins = [r for r in tail if r["outcome"] == "OURS WINS"]
    if covered != want:
        missing = sorted(want - covered)
        return False, f"last {len(tail)} rounds do not cover every lens (missing: {', '.join(missing) or 'n/a'})"
    if len(wins) != len(tail):
        lost = [r["lens"] for r in tail if r["outcome"] != "OURS WINS"]
        return False, f"the bar still wins on: {', '.join(lost)}"
    return True, "ours won every lens across a full rotation"


def deliverable_gates(text: str) -> tuple[list[str], list[str], list[str]]:
    """Split DELIVERABLE.md into (unchecked, blocked, done).

    A gate whose text still carries a `<placeholder>` counts as unchecked *and*
    unwritten — the template's own suggestions must be replaced with the real
    definition of done before they mean anything.
    """
    unchecked: list[str] = []
    blocked: list[str] = []
    done: list[str] = []
    for m in GATE_RE.finditer(text):
        mark, body = m.group(1).lower(), m.group(2).strip()
        if re.search(r"\bBLOCKED\b", body, re.I):
            blocked.append(body)
        elif mark == "x":
            done.append(body)
        else:
            unchecked.append(body)
    return unchecked, blocked, done


def facet_of(detail: str) -> str:
    m = FACET_RE.search(detail)
    return m.group(1).strip().lower() if m else ""


def facet_problems(pieces: list[tuple[str, str]]) -> list[str]:
    """Why this decomposition would produce a surface-only run.

    A piece is a promise of rounds: rounds are spent per piece, so a piece list that
    is all surface *is* a run that is all surface, however the goal was worded. This
    is the check that would have caught the classic "make an AAA game" run whose six
    pieces were all regions of one screenshot.
    """
    out: list[str] = []
    facets = [(n, facet_of(d)) for n, d in pieces]
    untagged = [n for n, f in facets if not f]
    if untagged:
        out.append("PIECES.md: no `facet:` on " + ", ".join(untagged[:4])
                   + (" …" if len(untagged) > 4 else "")
                   + " — tag every piece so the balance below can be checked")
        return out
    named = [f for _, f in facets]
    if "play" not in named:
        out.append("PIECES.md has no `facet: play` piece — nothing in this run works on what the "
                   "user actually does, so no number of rounds can turn it into a product")
    surface = [f for f in named if f in SURFACE_FACETS]
    if len(surface) * 2 > len(named):
        out.append(f"PIECES.md is {len(surface)}/{len(named)} surface pieces "
                   f"({', '.join(sorted(set(surface)))}) — at most half may be surface, or the "
                   f"rotation spends the run on how it looks")
    return out


def surface_drift(rounds: list[dict], pieces: list[tuple[str, str]], window: int) -> str:
    """Warn when the recent rounds have all gone to surface pieces anyway."""
    by_name = {n.strip().lower(): facet_of(d) for n, d in pieces}
    if not any(f and f not in SURFACE_FACETS for f in by_name.values()):
        return ""
    settled = [r for r in rounds if r["settled"]]
    if len(settled) < window:
        return ""
    tail = settled[-window:]
    fac = [by_name.get(r["piece"].strip().lower(), "") for r in tail]
    if fac and all(f in SURFACE_FACETS for f in fac):
        return (f"SURFACE DRIFT — the last {window} settled rounds all went to surface pieces "
                f"({', '.join(sorted(set(fac)))}). Non-surface pieces exist and are starving. "
                f"Work the next round on one of them, or `--rotate piece` from here.")
    return ""


def stall_warning(rounds: list[dict], window: int = 3) -> str:
    settled = [r for r in rounds if r["settled"] and r["gap"]]
    if len(settled) < window:
        return ""
    tail = settled[-window:]
    if len({normalise_gap(r["gap"]) for r in tail}) == 1:
        return (f"STALL — the same gap has come back {window} rounds running: "
                f"\"{tail[-1]['gap']}\". It is probably phrased as a feeling rather than an "
                f"observable difference, or the fix is not actually landing. Rewrite it as "
                f"\"the bar has X where ours has Y\", or log it BLOCKED and move on.")
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="What the next Gauntlet round should be")
    ap.add_argument("run", help="run directory, e.g. .gauntlet/<slug>")
    ap.add_argument("--json", action="store_true", help="emit machine-readable output")
    ap.add_argument("--rotate", choices=("lens", "piece"), default="lens",
                    help="lens: run a whole lens rotation on one piece, then move on (default). "
                         "piece: change piece every round.")
    args = ap.parse_args()

    run = Path(args.run)
    if not run.is_dir():
        print(f"error: no such run directory: {run}", file=sys.stderr)
        return 2

    bar_txt = read(run / "BAR.md")
    rubric_txt = read(run / "RUBRIC.md")
    pieces_txt = read(run / "PIECES.md")
    state_txt = read(run / "STATE.md")

    missing = [name for name, txt in
               (("BAR.md", bar_txt), ("RUBRIC.md", rubric_txt), ("PIECES.md", pieces_txt))
               if not txt.strip()]

    lenses = [n for n, _ in named_items(rubric_txt)]
    pieces = named_items(pieces_txt)
    if not lenses:
        missing.append("RUBRIC.md has no lenses (`- **name** — question`)")
    if not pieces:
        missing.append("PIECES.md has no pieces (`- **name** — capture: <cmd>`)")
    if pieces and any(is_placeholder(n) for n, _ in pieces):
        missing.append("PIECES.md still holds the template placeholder — write the real pieces")
    if pieces and not any(CAPTURE_RE.search(d) and not is_placeholder(CAPTURE_RE.search(d).group(1))
                          for _, d in pieces):
        missing.append("no piece has a real `capture:` command — without one there is nothing "
                       "for a critic to look at, and the round grades a description instead")

    kind = field(state_txt, "KIND").lower()
    is_product = kind in PRODUCT_KINDS
    deliv_txt = read(run / "DELIVERABLE.md")
    gates_todo, gates_blocked, gates_done = deliverable_gates(deliv_txt)
    gates_todo_real = [g for g in gates_todo if not is_placeholder(g)]
    gates_unwritten = [g for g in gates_todo if is_placeholder(g)]

    if is_product:
        if not deliv_txt.strip():
            missing.append("DELIVERABLE.md is missing — a product run needs a definition of done, "
                           "or its rounds go to whatever facet is easiest to look at")
        elif not (gates_todo or gates_done or gates_blocked):
            missing.append("DELIVERABLE.md has no gates (`- [ ] <what must be true> — check: <cmd>`)")
        if pieces:
            missing.extend(facet_problems(pieces))

    rounds = load_rounds(run)
    done = len([r for r in rounds if r["settled"]])
    pending = [r for r in rounds if not r["settled"]]

    goal, bar_line, ref_rel = field(bar_txt, "GOAL"), field(bar_txt, "BAR"), field(bar_txt, "REFERENCE")
    deliverable = field(bar_txt, "DELIVERABLE")
    if not deliverable or is_placeholder(deliverable):
        missing.append("BAR.md has no DELIVERABLE line — one sentence on what the user actually "
                       "holds at the end. It is checked against KIND by whoever reads it, not by "
                       "this script, and that reading is the only thing standing between a product "
                       "goal and a run shaped to polish one facet of it")
    ref_rel = ref_rel.split("#")[0].strip()
    ref_path = (run / ref_rel) if ref_rel else None
    if bar_line and is_placeholder(bar_line):
        missing.append("BAR.md still has the placeholder bar — decide the standard first")
    if ref_path is None or not ref_path.is_file():
        missing.append(f"BAR.md REFERENCE does not resolve to a file "
                       f"({ref_rel or 'empty'}) — a bar that cannot be opened cannot be compared against")

    bm = BUDGET_RE.search(state_txt)
    budget = int(bm.group(1) or bm.group(2)) if bm else None

    idx = done
    lens = piece_name = capture_template = ""
    lens_pos = 0
    if lenses and pieces:
        lens = least_recent(lenses, [r["lens"] for r in rounds if r["settled"]])
        lens_pos = lenses.index(lens) + 1
        piece_name, detail = pick_piece(pieces, rounds, lenses, args.rotate)
        cm = CAPTURE_RE.search(detail)
        capture_template = cm.group(1).strip() if cm else ""

    nxt = idx + 1
    nxt_name = str(nxt).zfill(pad_for(budget or nxt))
    nxt_dir = run / "rounds" / nxt_name

    ext = ""
    if ref_path and ref_path.suffix:
        ext = ref_path.suffix
    else:
        for r in reversed(rounds):
            hit = sorted(r["dir"].glob("artifact.*"))
            if hit:
                ext = hit[0].suffix
                break
    ext = ext or ".png"
    artifact_path = nxt_dir / ("artifact" + ext)
    capture = render_capture(capture_template, artifact_path, nxt_dir, nxt_name)

    rotation_done, rotation_why = clean_rotation(rounds, lenses)
    stall = stall_warning(rounds)
    # One full rotation on a surface piece is legitimate under the default rotation, so
    # only a run of *more* than a rotation counts as drift.
    drift = surface_drift(rounds, pieces, max(4, len(lenses) + 1)) if is_product else ""
    blocked = [ln.strip() for ln in read(run / "open_gaps.md").splitlines()
               if ln.strip().lstrip("-*[ ]x").upper().startswith("BLOCKED")]
    over_budget = budget is not None and done >= budget

    stop = []
    if rotation_done:
        stop.append(f"CLEAN ROTATION — {rotation_why}")
    if over_budget:
        stop.append(f"BUDGET SPENT — {done}/{budget} rounds")

    ab_cmd = shlex.join([
        "python3", str(SCRIPTS / "ab.py"),
        "--round", str(nxt_dir),
        "--ref", str(ref_path) if ref_path else "<ref>",
        "--cand", str(artifact_path),
        "--squint",
    ])

    piece_facet = ""
    if piece_name:
        piece_facet = facet_of(dict((n.strip().lower(), d) for n, d in pieces)
                               .get(piece_name.strip().lower(), ""))

    payload = {
        "run": str(run), "goal": goal, "bar": bar_line, "kind": kind,
        "deliverable_text": deliverable,
        "reference": str(ref_path) if ref_path else "",
        "rounds_done": done, "budget": budget,
        "next_round": nxt_name, "next_dir": str(nxt_dir),
        "lens": lens, "piece": piece_name, "facet": piece_facet,
        "capture_template": capture_template, "capture": capture,
        "artifact": str(artifact_path),
        "ab_command": ab_cmd,
        "deliverable_gates": {"todo": gates_todo_real, "unwritten": gates_unwritten,
                              "blocked": gates_blocked, "done": gates_done},
        "stop": stop, "stall": stall, "drift": drift, "blocked": blocked, "missing": missing,
        "pending_rounds": [r["name"] for r in pending],
        "recent": [{"round": r["name"], "lens": r["lens"], "outcome": r["outcome"], "gap": r["gap"]}
                   for r in rounds[-5:]],
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1 if missing else 0

    print(f"run: {run}")
    if goal:
        print(f"goal: {goal}")
    if bar_line:
        print(f"bar:  {bar_line}")

    # Printed together, every round, on purpose. No script can tell from a sentence
    # whether a run is aimed at a whole product — but a reader can, in a second, and
    # this run shape is the one decision that cannot be repaired by later rounds. So
    # it gets re-presented rather than re-guessed: a Goal continuation after compacted
    # context sees the choice again instead of inheriting it silently.
    if deliverable:
        print(f"\ndeliverable: {deliverable}")
        print(f"run shape:   KIND: {kind or '(unset)'} — "
              + ("whole product; rounds must cover it, not just its surface"
                 if is_product else
                 "one facet. If the deliverable above is a whole thing someone uses, this is the"
                 " wrong shape — stop and reinitialise with --kind game/product."))

    if missing:
        print("\nSETUP INCOMPLETE — phases 1–4 have not finished:")
        for m in missing:
            print(f"  - {m}")
        print("\nFinish the setup before looping. An unattended run that starts without a frozen")
        print("bar and rubric spends the night polishing whatever it happened to guess at 3am.")
        return 1

    if is_product and (gates_todo_real or gates_unwritten):
        n = len(gates_todo_real) + len(gates_unwritten)
        print(f"\nDELIVERABLE INCOMPLETE — {n} gate(s) in DELIVERABLE.md not ticked. "
              f"{len(gates_done)} done, {len(gates_blocked)} blocked.")
        if gates_unwritten:
            print("\n  still the template (write the real gate, then close it):")
            for g in gates_unwritten[:10]:
                print(f"    - {g}")
        if gates_todo_real:
            print("\n  outstanding:")
            for g in gates_todo_real[:10]:
                print(f"    - {g}")
        print("\nThis is the next work — close the first outstanding gate, verify its `check:`,")
        print("tick it, and run this again. Quality rounds do not open on a product that is not")
        print("yet the thing that was asked for; polishing the surface of an incomplete product")
        print("is how a run delivers a beautiful screenshot instead of a game.")
        print("If a gate genuinely cannot be met here, mark it BLOCKED: <why> and it stops blocking.")
        return 1

    if pending:
        print(f"\nUNFINISHED ROUND: {', '.join(r['name'] for r in pending)} — no outcome.json.")
        print("Finish it (commit the verdict, then reveal.py) before opening a new round.")

    print(f"\nrounds settled: {done}" + (f" / {budget} budgeted" if budget else ""))
    if payload["recent"]:
        print("recent:")
        for r in payload["recent"]:
            print(f"  {r['round']}  {r['outcome']:<10} {r['lens']}")

    print(f"\nNEXT ROUND: {nxt_name}")
    print(f"  lens:    {lens}   ({lens_pos} of {len(lenses)}, longest unused)")
    print(f"  piece:   {piece_name}" + (f"   [facet: {piece_facet}]" if piece_facet else ""))
    if capture:
        print(f"  capture: {capture}")
    else:
        print("  capture: (none recorded in PIECES.md — add `capture: <cmd>` so rounds stay comparable)")
    print(f"  into:    {payload['artifact']}")
    print(f"\n  {ab_cmd}")

    if stall:
        print(f"\n{stall}")
    if drift:
        print(f"\n{drift}")
    if is_product and gates_blocked:
        print(f"\ndeliverable gates marked BLOCKED: {len(gates_blocked)} — these ship unmet unless "
              f"they are reopened. Say so in the final report.")
    if blocked:
        print(f"\nblocked gaps carried in open_gaps.md: {len(blocked)}")

    print("\nSTOP CHECK:")
    if stop:
        for s in stop:
            print(f"  {s}  → stop and report.")
    else:
        print(f"  keep going — {rotation_why}.")
        print("  (Also stop if two rounds running the honest biggest gap is merely cosmetic —")
        print("   that judgement is yours, not this script's.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
