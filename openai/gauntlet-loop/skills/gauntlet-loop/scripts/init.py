#!/usr/bin/env python3
"""Create the skeleton for a Gauntlet run.

Writes the run directory with BAR.md, RUBRIC.md, PIECES.md, STATE.md and
open_gaps.md already in the shape the other scripts parse, copies the reference
into ref/, and prints what still needs a human decision.

The point is not to save a few file writes. It is that ab.py, reveal.py,
progress.py and next.py all read these files by pattern — a hand-written
RUBRIC.md whose lenses are prose instead of `- **name** — question` bullets
leaves next.py unable to rotate, and that failure shows up at 3am rather than now.

Nothing here is overwritten if it already exists, so running it twice on a live
run is safe.

Usage:
  init.py .gauntlet/<slug> --goal "..." [--bar "..."] [--ref path/to/reference.png]
          [--kind game|product|image|ui|model3d|gamefeel|video|text|spec|code]

`--kind game` and `--kind product` additionally write DELIVERABLE.md — the
definition of done for the *product*. next.py refuses to open a quality round
while any of its gates is unchecked, which is what stops a "make an AAA game"
run from spending forty rounds on a screenshot of a game.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Starter lens sets per domain. These are drafts, not answers: a rubric has to be
# derived from the bar that was actually chosen, or it grades a generic idea of
# quality instead of the specific distance to this standard.
LENSES: dict[str, list[tuple[str, str]]] = {
    "game": [
        ("core loop", "watch 30 seconds of each: what does the bar's loop make you want to do next that ours does not?"),
        ("control feel", "input to response — latency, curve, weight. Does the thing you steer feel connected or driven-by-numbers?"),
        ("challenge & pacing", "can you lose? does pressure rise? where does the bar spike and settle, and where is ours flat?"),
        ("feedback", "every action answered in sound, motion and UI — which layers does the bar have that ours lacks?"),
        ("session shape", "start to end of one session: onboarding, a reason to press restart, something carried forward"),
        ("presentation", "the frame and the interface — hierarchy, material, light, type. One lens of six, not the whole run"),
    ],
    "product": [
        ("core job", "the one thing a user comes for: how many steps and how much doubt, ours vs the bar?"),
        ("first run", "cold start to first success, with nobody explaining anything"),
        ("completeness", "which paths dead-end, 404, or silently do nothing on ours and not on the bar?"),
        ("responsiveness", "latency and feedback on every action, including the slow and failing ones"),
        ("state & recovery", "refresh, back, offline, bad input, half-finished work — what survives?"),
        ("presentation", "hierarchy, spacing, type, visual language. One lens of six, not the whole run"),
    ],
    "image": [
        ("silhouette", "at 128px, does it read as the same thing at all? — look at the squint pair"),
        ("value structure", "are the light and dark masses arranged like the bar's? — squint, ignore hue"),
        ("detail density", "does ours carry as much information per area, or is it emptier?"),
        ("colour & material", "do surfaces read as the same substance under the same light?"),
        ("cohesion", "one authored image, or parts assembled? — look for mismatched styles"),
    ],
    "ui": [
        ("hierarchy", "what does the eye hit first, and is it the same thing as on the bar?"),
        ("spacing rhythm", "is the spacing a system or a series of one-off numbers?"),
        ("type scale", "do the sizes and weights come from one scale? — compare headings to body"),
        ("state completeness", "hover, empty, error, loading — which exist on the bar and not on ours?"),
        ("visual language", "does it belong to this product, or to a generic template?"),
    ],
    "model3d": [
        ("silhouette", "at 128px, does the outline read as the reference subject?"),
        ("proportion", "limb and part ratios against the reference, measured not felt"),
        ("completeness", "what exists on the bar and simply is not modelled on ours?"),
        ("surface & material", "does it respond to light like the reference material?"),
        ("animation-readiness", "does the rig survive a test pose without collapsing?"),
    ],
    "gamefeel": [
        ("impact", "does a hit read in a single frame? — compare frame samples at contact"),
        ("anticipation & follow-through", "is there a wind-up and a settle, or does motion just start and stop?"),
        ("feedback layering", "sound, shake, particles, hitstop — which layers does the bar have that ours lacks?"),
        ("readability under clutter", "at peak chaos, can you still tell what happened?"),
        ("restraint", "does the juice stack into noise? — more is a loss if the bar is calmer and reads better"),
    ],
    "video": [
        ("pacing", "does a cut ever arrive late? — compare shot lengths against the bar"),
        ("frame composition", "sample stills: would each hold on its own?"),
        ("transition craft", "do transitions carry meaning or just fill a gap?"),
        ("text legibility in motion", "can every caption be read at speed, at phone size?"),
        ("first three seconds", "what does the bar do in its opening that ours does not?"),
    ],
    "text": [
        ("first paragraph", "does the opening earn the second paragraph?"),
        ("claim density", "how many load-bearing claims per screen, ours vs the bar?"),
        ("concreteness", "specifics or adjectives? — count the unfalsifiable sentences"),
        ("rhythm", "read both aloud: where does ours become a slog?"),
        ("ending", "does it land, or does it just stop?"),
    ],
    "spec": [
        ("unambiguity", "pick three requirements: can each be read two ways by a stranger?"),
        ("verifiability", "could a tester prove each requirement met without asking the author?"),
        ("edge coverage", "empty, huge, offline, concurrent, hostile — which does the bar handle and ours skip?"),
        ("decomposition", "could two people build from this in parallel without colliding?"),
        ("rationale", "does it say why, so a builder can resolve a case it did not foresee?"),
    ],
    "code": [
        ("hot path cost", "the benchmark number, ours vs the bar"),
        ("allocation churn", "what gets allocated per call that need not be?"),
        ("API surface", "would a stranger misuse it? — read the signatures cold"),
        ("failure behaviour", "what happens on bad input, and is that a decision or an accident?"),
        ("test honesty", "break the implementation on purpose — do the tests actually fail?"),
    ],
}

GATES: dict[str, str] = {
    "game": ("every DELIVERABLE.md gate still ticks; the game boots from its entry command with no "
             "console errors; a scripted session plays start→end and writes its metrics; frame rate "
             "holds its target; no softlock, no dead menu"),
    "product": ("every DELIVERABLE.md gate still ticks; build, typecheck, lint and tests pass; the "
                "end-to-end script completes the core job on a cold start; no console or server errors"),
    "image": "the export succeeds; file non-empty; dimensions match the reference aspect",
    "ui": "renders with no overflow; no horizontal body scroll; contrast ratios pass",
    "model3d": "scene builds; no NaN transforms; poly budget; render is not blank",
    "gamefeel": "the clip records; frame rate holds; no console errors",
    "video": "render completes; loudness target; no dropped frames; duration sane",
    "text": "length window; no placeholders left; links resolve; spellcheck",
    "spec": "every requirement has an ID and a check; no TBD left; all open questions answered",
    "code": "builds; tests pass; lint clean; the benchmark runs",
}


# Kinds whose deliverable is a whole product rather than one facet of one. These get
# DELIVERABLE.md, and next.py will not open a quality round while a gate there is
# unchecked — the failure this guards against is a run that polishes the surface of
# something that is not yet the thing the user asked for.
PRODUCT_KINDS = {"game", "product"}

# Facet vocabulary for PIECES.md in product runs. next.py parses `facet: <name>` and
# refuses a decomposition that is mostly surface, because a set of pieces is a set of
# rounds: whatever is not a piece never gets a round spent on it.
FACETS = {
    "play": "mechanics, the loop itself, control feel, difficulty — what the user actually does",
    "meta": "progression, save, economy, unlocks, session-to-session carry",
    "content": "how much there is and how varied — levels, tracks, enemies, copy, data",
    "ux": "flow between screens, onboarding, menus, settings, error paths",
    "audio": "music, SFX, mix — the half of feel that is not visible",
    "visual": "the frame: world, materials, light, effects, grade",
    "perf": "frame rate, load time, memory, stability across a long session",
}

PIECES_TEMPLATE = """# Pieces

One line per piece. `capture:` is the frozen command that turns that piece into
something a critic can look at — freeze it now and reuse it every round, because
a capture that changes between rounds makes improvement indistinguishable from
reframing.

- **<piece name>** — capture: <command writing to {artifact}>
"""

PIECES_PRODUCT_TEMPLATE = """# Pieces

One line per piece, in the syntax below — `facet:` first, `capture:` last, because
next.py parses the command as everything after `capture:`.

    - **<name>** — facet: play — capture: <command writing to {{artifact}}>

**A piece is a promise of rounds.** Rounds are spent per piece, so whatever is not
a piece here simply never gets worked on. This is where a "make it AAA" run quietly
turns into a screenshot run: six visual pieces means six visual rounds per rotation
and nothing ever spent on the thing being played.

So the decomposition has to cover the product, not its surface. next.py enforces the
floor: at least one `play` piece, and surface pieces (`visual` + `ux`) no more than
half the total. Facets available:

{facet_help}

Order matters — pieces are worked in the order listed and the first one takes round 1.
Put the piece the product most fails to *be* at the top; put `visual` last.

- **<the core loop>** — facet: play — capture: <a scripted session writing {{artifact}} plus metrics under {{round_dir}}>
- **<what carries between sessions>** — facet: meta — capture: <command writing {{artifact}}>
- **<how much there is to do>** — facet: content — capture: <command writing {{artifact}}>
- **<the flow a new player walks through>** — facet: ux — capture: <command writing {{artifact}}>
- **<the sound of it>** — facet: audio — capture: <command writing {{artifact}}>
- **<the frame>** — facet: visual — capture: <command writing {{artifact}}>
"""

DELIVERABLE_TEMPLATE = """# Deliverable — what "done" means for this product

The definition of done, written before round 1 and ticked as it is met. **next.py
will not open a quality round while any gate here is unchecked.** That refusal is
the point of this file: a gauntlet is a polishing loop, and polishing something
that cannot yet be played end to end produces a beautiful thing that is not the
thing that was asked for.

Syntax — one gate per line, and a `check:` that says how it is verified:

    - [ ] <what must be true of the product> — check: <command, or `manual: <what to do>`>

Rules:

- Gates are **must-haves for a shippable product**, not wishes. Aim for 8–12. Every
  extra gate is a quality round that does not happen.
- A gate that genuinely cannot be met here gets `BLOCKED: <why>` in its text; next.py
  reports it and stops treating it as a blocker, so the run moves on honestly rather
  than grinding.
- Adding a gate mid-run is allowed and gets a line in STATE.md. Deleting one to
  unblock the loop is the same move as softening the rubric — don't.
- Tick a gate only when its `check:` actually passes. These are re-checked as free
  gates every round, so a regression pulls the run back off polish and onto the product.

## Gates

- [ ] The product starts from one documented command on a clean machine — check: <cmd>
- [ ] A first-time user reaches the core activity without being told how — check: manual: <what to do>
- [ ] One full session runs start → end with no dead end, softlock or empty screen — check: <cmd>
- [ ] It is possible to fail / be wrong, and the product says so — check: <cmd>
- [ ] Progress or state survives a reload — check: <cmd>
- [ ] Every action answers with feedback (sound and motion, or an explicit result) — check: <cmd>
- [ ] There is enough content that a session does not run out — check: <cmd>
- [ ] It holds its performance target for a full session — check: <cmd>
- [ ] Nothing in the shipped build is placeholder, debug, or lorem — check: <cmd>
- [ ] It runs on the target device/browser it is meant for — check: <cmd>

Replace every line above with the real gates for *this* product; the list is a
prompt, not a spec. Anything with an angle-bracket placeholder still counts as
unwritten and next.py will say so.
"""


def write_if_absent(path: Path, body: str, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(path.name)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    created.append(path.name)


def gitignore(run: Path) -> str:
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             cwd=run.parent, capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    root = Path(top.stdout.strip())
    gi = root / ".gitignore"
    line = ".gauntlet/"
    if gi.is_file() and line in gi.read_text(errors="replace"):
        return ""
    with gi.open("a") as fh:
        fh.write(("" if not gi.exists() or gi.read_text(errors="replace").endswith("\n") else "\n")
                 + line + "\n")
    return str(gi)


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a Gauntlet run skeleton")
    ap.add_argument("run", help="run directory, e.g. .gauntlet/<slug>")
    ap.add_argument("--goal", required=True, help="what we are making, one line")
    ap.add_argument("--deliverable", default="",
                    help="what the user actually has at the end — the thing they will use, "
                         "one sentence. Written into BAR.md and re-read by next.py every round, "
                         "next to KIND, so the run shape stays a stated decision rather than an "
                         "assumption nobody revisits.")
    ap.add_argument("--bar", default="", help="the standard, one sentence, and why it is the right one")
    ap.add_argument("--ref", default="", help="reference file to copy into ref/")
    ap.add_argument("--kind", required=True, choices=sorted(LENSES),
                    help="domain — picks the starter lens set and free gates. Required on purpose: "
                         "it used to default to `image`, and a forgotten flag turned a product goal "
                         "into a render run without anything ever saying so.")
    ap.add_argument("--budget", type=int, default=0, help="round budget to record in STATE.md")
    args = ap.parse_args()

    run = Path(args.run)
    (run / "rounds").mkdir(parents=True, exist_ok=True)
    (run / "ref").mkdir(parents=True, exist_ok=True)

    ref_line = "REFERENCE:"
    if args.ref:
        src = Path(args.ref)
        if not src.is_file():
            print(f"error: --ref not found: {src}", file=sys.stderr)
            return 2
        dst = run / "ref" / src.name
        if not dst.exists():
            shutil.copyfile(src, dst)
        ref_line = f"REFERENCE: ref/{src.name}"

    created: list[str] = []
    skipped: list[str] = []

    write_if_absent(run / "BAR.md", f"""# The bar

DELIVERABLE: {args.deliverable or "<TODO: what the user has at the end — the thing they will use>"}
GOAL: {args.goal}
BAR: {args.bar or "<TODO: the standard in one sentence, and why it is the right one>"}
{ref_line}

The DELIVERABLE line and KIND are checked against each other, by a reader rather than
by a regex: next.py prints them side by side every round. If the deliverable is a whole
thing someone uses and KIND names one facet of it, the run is the wrong shape and no
number of rounds fixes that — reinitialise rather than continue.

Why this bar: <one sentence. If it takes a paragraph, it is not concrete enough
to compare against.>

Rejected alternative: <what else was considered, and why this one won.>
""", created, skipped)

    lens_body = "\n".join(f"- **{n}** — {q}" for n, q in LENSES[args.kind])
    write_if_absent(run / "RUBRIC.md", f"""# Rubric — frozen before round 1

Round N uses lens N % {len(LENSES[args.kind])}. Stricter-only from here: every edit
gets a line in STATE.md saying what changed and why. A rubric that softens over a
run is how a gauntlet declares victory over a bar it never met.

Starter set for `{args.kind}` — adapt each line to *this* bar before round 1,
otherwise it grades a generic idea of quality rather than the distance to this
specific standard.

{lens_body}

## Free gates (checked every round, before any critic)

{GATES[args.kind]}
""", created, skipped)

    is_product = args.kind in PRODUCT_KINDS
    if is_product:
        facet_help = "\n".join(f"- `{n}` — {d}" for n, d in FACETS.items())
        pieces_body = PIECES_PRODUCT_TEMPLATE.format(facet_help=facet_help)
    else:
        pieces_body = PIECES_TEMPLATE
    write_if_absent(run / "PIECES.md", pieces_body, created, skipped)

    if is_product:
        write_if_absent(run / "DELIVERABLE.md", DELIVERABLE_TEMPLATE, created, skipped)

    budget_line = (f"- Budget: stop after round {args.budget}.\n" if args.budget else
                   "- Budget: <N rounds, or 'until the user stops it'>\n")
    write_if_absent(run / "STATE.md", f"""# Gauntlet run — {run.name}

On a Codex Goal continuation, call `get_goal` and then read this file. The active
Goal owns the lifecycle; this file is the detailed round memory and survives
harness compaction.

GOAL: {args.goal}
KIND: {args.kind}

## Rules for this run

{budget_line}- Rounds per Goal turn: 3, then persist state and yield.
- Rubric is stricter-only. Log every edit here with the reason.

## Codex Goal lifecycle

- Create or reuse a Goal only when the user explicitly requested a persistent
  gauntlet/loop run.
- Never equate this run's round budget with a Goal token budget.
- Mark the Goal complete only when its stated objective is actually achieved.

## Decisions taken without asking

<one line each, so the morning review can see what was guessed and when>

## Ledger
""", created, skipped)

    write_if_absent(run / "open_gaps.md", """# Open gaps

The queue. Everything noticed during a round that was not that round's single
target lands here, so the round stays one change wide and attribution survives.

Prefix a line with `BLOCKED:` when a gap genuinely cannot be closed here — a
missing asset, a tool that will not run — so the run moves on instead of grinding.

""", created, skipped)

    gi = gitignore(run)

    print(f"run skeleton: {run}")
    if created:
        print(f"  created: {', '.join(created)}")
    if skipped:
        print(f"  left alone (already existed): {', '.join(skipped)}")
    if gi:
        print(f"  added .gauntlet/ to {gi}")

    print("\nStill needs a decision before round 1:")
    if not args.deliverable:
        print("  - BAR.md: the DELIVERABLE line is a TODO — write what the user ends up holding,")
        print(f"    then read it back against KIND: {args.kind} and confirm that is the right shape")
    if not args.bar:
        print("  - BAR.md: the bar sentence is a TODO")
    if not args.ref:
        print("  - ref/ is empty — a bar that cannot be opened cannot be compared against")
    print(f"  - RUBRIC.md: adapt the {len(LENSES[args.kind])} starter lenses to this bar")
    print("  - PIECES.md: real pieces with a frozen capture command each; use {artifact} for")
    print("    the per-round output path ({round_dir} and {round} are also available)")
    if is_product:
        print("  - PIECES.md: at least one `facet: play` piece; surface pieces (visual+ux) at most half")
        print("  - DELIVERABLE.md: the real definition of done — no quality round opens until every")
        print("    gate there is ticked, which is what keeps a product run from becoming a render run")
        print("  - build the vertical slice first: the whole product, end to end, ugly but complete")
    print(f"\nThen: python3 {Path(__file__).resolve().parent / 'next.py'} {run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
