#!/usr/bin/env python3
"""Create the skeleton for a gamemaker run.

Writes every file of the run in the exact shape the other scripts parse, so that
next.py can tell which rung of the ladder the run is on, contract.py can count
what exists against what was promised, and progress.py can draw it.

The point is not to save file writes. It is that hand-written files break the
run silently: a LADDER.md whose stage headers do not match `## Stage N — NAME`
leaves next.py unable to find the current stage, and that surfaces at 3am on a
night run rather than now.

Nothing is overwritten if it already exists, so running this twice on a live run
is safe.

Usage:
  init.py .gamemaker/<slug> --ambition "клон Need for Speed" --scale full \\
          [--reference "Need for Speed: Most Wanted"] [--stack web] \\
          [--platform "browser, desktop + mobile"] [--budget 200]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# The ladder. Fixed on purpose: the order is what turns an ambition into a game
# rather than into a polished fragment of one. Each stage owns files (which must
# be free of `<placeholders>` before it can close) and carries explicit gates.
#
# `files:` is auto-checked by next.py. The `- [ ]` gates are the substantive ones
# a human or a command has to satisfy.
LADDER = """# Ladder — the spine of this run

Seven stages, worked in order. A stage closes when its files carry no
`<placeholders>` **and** every gate under it is ticked. next.py finds the current
stage by taking the first one that is not closed, and it will not hand out work
from a later stage — which is the whole reason this file exists.

Ticking a gate whose check does not actually pass is the one move that breaks
this run beyond repair: every later stage is built on the assumption that the
earlier ones are true.

A gate that genuinely cannot be met in this environment gets `BLOCKED: <why>` in
its text. It stops blocking, it is reported at the end, and it is never deleted —
a deleted gate is a lowered standard that leaves no trace.

## Stage 0 — BRIEF
files: BRIEF.md, CONTRACT.md
- [ ] the contract's numbers were taken from the reference title's real inventory, not from what feels achievable tonight — check: manual: name the source of each number
- [ ] the ambition has been read as a scale decision and the decision is stated in BRIEF.md — check: manual

## Stage 1 — DESIGN
files: PILLARS.md, DESIGN.md, ART.md
- [ ] every system in DESIGN.md names the pillar it serves; none serves nothing — check: manual: read the systems list against PILLARS.md
- [ ] the design holism checklist has been run and its findings are in open_gaps.md — check: manual: see references/design.md
- [ ] the core loop is written at all three scales — 30 seconds, 5–15 minutes, one session — check: manual
- [ ] ART.md names a direction, a palette in hex, and at least three signature techniques a generic genre-mate would not have — check: manual: run the anti-generic check in references/art.md

## Stage 2 — HARNESS
files: HARNESS.md, BARS.md
- [ ] the project builds and starts from one documented command — check: <cmd>
- [ ] preflight passes: the session runs twice headless with one seed and identical gameplay metrics, the screenshot lands, ab.py builds a pair — check: python3 <skill>/scripts/preflight.py <run>
- [ ] every facet in BARS.md has a bar that can be opened, or is explicitly BLOCKED — check: manual

## Stage 3 — SLICE
files: (none)
- [ ] one full cycle start → challenge → resolution is playable end to end — check: <cmd>
- [ ] the session lasts 3–5 minutes without repeating itself — check: <cmd>
- [ ] it is possible to lose or get it wrong, and the game says so — check: <cmd>
- [ ] a first-time player reaches the core activity without being told how — check: manual: read the first-session filmstrip
- [ ] the validation question in STATE.md is answered, and the verdict is PROCEED — check: manual

## Stage 4 — SYSTEMS
files: (none)
- [ ] every `tier: mvp` system in DESIGN.md exists and its check passes — check: manual: run each system's check
- [ ] state survives a reload — check: <cmd>
- [ ] no path dead-ends: every screen has a way out and every failure is visible — check: <cmd>
- [ ] no un-seeded randomness in gameplay code (references/code.md rule 1; adapt the paths to this project) — check: ! grep -rn 'Math.random(' src/systems/ src/content/ 2>/dev/null
- [ ] simulation does not import rendering (adapt to the stack) — check: ! grep -rnE 'import .*render|from .*render' src/systems/ 2>/dev/null
- [ ] tuning numbers live in data files, not inline in systems — check: manual: references/code.md rule 3, spot-check the largest system

## Stage 5 — CONTENT
files: (none)
- [ ] every line of CONTRACT.md is met or explicitly BLOCKED — check: python3 <skill>/scripts/contract.py <run>
- [ ] the content is varied, not the same unit renamed N times — check: manual

## Stage 6 — POLISH
files: RUBRIC.md
- [ ] our side wins the blind A/B on every lens across one full rotation, on every facet — check: manual: see STATE.md ledger
- [ ] nothing in open_gaps.md is still an unexplained loss to the bar — check: manual

## Stage 7 — SHIP
files: (none)
- [ ] a soak session of the target length shows no leak, no fps drift, no state rot — check: <cmd>
- [ ] nothing in the build is placeholder, debug, lorem or a console log — check: <cmd>
- [ ] every action answers in sound and motion — check: manual
- [ ] the platform's own requirements are met — check: manual: see references/ship.md
"""

BRIEF = """# Brief — frozen after stage 0

The only stage that may talk to the user. Everything below is decided once and
then read, never re-litigated: re-deriving a brief mid-run quietly resets the
standard and nothing downstream notices.

AMBITION: {ambition}
REFERENCE TITLE: {reference}
SCALE: {scale}
STACK: {stack}
PLATFORM: {platform}
SESSION: <how long one session is, and what shape it has: a run, a match, a level, an evening>

## How the scale was read

<One paragraph. The ambition's wording sets the floor: a named commercial title
means the full game and the contract is derived from that title's real inventory.
"a small prototype of X" means a slice. If the wording is ambitious and the scale
here says slice, that is a decision that needs a sentence of defence — the usual
cause is the run flinching, not the user asking for less.>

## What the player is doing, in one sentence

<The core activity. If this sentence needs an "and", the game has two cores and
one of them is going to starve.>
"""

CONTRACT = """# Scope contract — the floor, in numbers

What "a whole game" means for this run, as counts taken from the reference title.
This file exists because a polished single level will pass every quality lens and
still not be the thing that was asked for. **The run may not report done while a
line here is open.**

Syntax — one line each, and a `count:` that prints a number:

    - [ ] <name>: <target> <unit> — count: <shell command printing a number>

Rules, and they are the entire point of the file:

- Numbers come **from the reference**, not from what fits in one night. If the
  reference ships 20 cars, the target is derived from 20 — the run may argue for
  a fraction and write the reasoning here, but it may not quietly pick 3.
- A line that cannot be met here gets `BLOCKED: <why>` in its text. It stops
  blocking, it is reported at the end, and it is **never deleted**. contract.py
  keeps a baseline and will say so if a line disappears.
- `count:` should be a real command wherever possible — a file count, a JSON
  array length, a grep. A counted line is verified every round for free; a
  `manual:` line is a promise nobody checks.
- Ticking a line whose count does not reach its target is the same move as
  deleting it.

## Reference inventory

<What the reference title actually ships, listed before any target is chosen.
This is the anti-lowball step: write down what the real game has, then decide
what fraction this run commits to and why. Skipping straight to targets is how a
"clone of NFS" becomes three tracks and a menu.>

## Contract

- [ ] <content unit, e.g. tracks>: <N> <unit> — count: <cmd printing a number>
- [ ] <second content unit, e.g. cars>: <N> <unit> — count: <cmd printing a number>
- [ ] <variety unit, e.g. race types>: <N> <unit> — count: <cmd printing a number>
- [ ] <meta system count, e.g. upgrade tiers>: <N> <unit> — count: <cmd printing a number>
- [ ] <audio, e.g. distinct SFX>: <N> <unit> — count: <cmd printing a number>
- [ ] <UX, e.g. screens with a finished state>: <N> <unit> — count: <cmd printing a number>
- [ ] <session length in minutes before content repeats>: <N> min — count: <cmd printing a number>
"""

PILLARS = """# Pillars — frozen after stage 1

Three to five non-negotiable principles that define what this game **is**. Every
design, art, audio and code decision has to serve at least one. A system that
serves none is scope creep with a nice name.

A pillar earns its place only if it is:

- **falsifiable** — "fun combat" is not a pillar; "combat rewards patience over
  aggression" is, because it makes a claim that a build can contradict;
- **constraining** — if it never forces a "no", it is decoration;
- **cross-departmental** — a pillar that says nothing about art, audio and code
  is only half a pillar;
- **memorable** — if they cannot be recited from memory, there are too many.

For software rather than a game, the same test applies: "state survives a
reload", "no screen ever blocks on a spinner", "every error says what to do next".

Anti-pillars are what this thing deliberately will **not** do. They are worth as
much as the pillars, because they are what a 3am decision gets checked against.

## Pillars

- **<name>** — <the falsifiable claim it makes about this game>
- **<name>** — <...>
- **<name>** — <...>

## Anti-pillars

- <what this game will deliberately not do, however tempting>
- <...>
"""

DESIGN = """# Design — frozen after stage 1

## Core fantasy

<What the player gets to be or do here that they cannot elsewhere, in one
visceral sentence. "You are a lone survivor building a life in a hostile
wilderness", not "an engaging survival experience".>

## The loop, at three scales

The nested-loop model is what makes the play facet decomposable. Each scale
fails differently, so each one is worth its own work.

- **30 seconds** — <the action that has to be satisfying on its own, before any
  reward exists. If this is not good, nothing built on top of it rescues it.>
- **5–15 minutes** — <the goal → effort → reward cycle. What is the unit of
  "one more"?>
- **one session** — <what progresses, where the natural stopping point is, and
  what makes someone come back tomorrow.>

## Difficulty philosophy

<One of: difficulty is the product (overcoming it is the reward) · accessible
entry with opt-in depth · difficulty serves narrative pacing · relaxed
engagement. State which, then say what the player is allowed to feel and for how
long before the design has to intervene.>

**Axes** — <name every independent dimension of challenge: execution, decision
complexity, resource pressure, time pressure, information. Tuning only execution
while decision complexity is overloaded reads to a player as "confusing", not as
"hard".>

## Economy

<Every resource, its sources (faucets) and its sinks. A resource with a source
and no sink becomes meaningless by mid-game; a sink with no source becomes a
wall. Write the flow rates even if they are guesses — a wrong number can be
corrected, an absent one cannot.>

## Systems

One line each, in the syntax below. next.py reads `tier:` to build stage 4's work
list and `pillar:` to catch systems that serve nothing.

    - **<name>** — tier: mvp — pillar: <pillar name> — check: <cmd or manual: ...>

`tier: mvp` is what stage 4 must ship. `tier: full` is everything else — real,
planned, and not blocking the ladder.

- **<system>** — tier: mvp — pillar: <which pillar> — check: <cmd>
- **<system>** — tier: mvp — pillar: <which pillar> — check: <cmd>
- **<system>** — tier: full — pillar: <which pillar> — check: <cmd>
"""

BARS = """# Bars — one per facet

A game has no single bar. Screenshots say what a game looks like and nothing at
all about what it plays like, and what it plays like is most of what "AAA" means.
So each facet gets its own standard, and the visual one is one of eight — with
its own twist: its bar is the ceiling of the stack plus ART.md's signatures,
not parity with the reference (references/art.md).

Syntax — next.py reads this to pick the round's capture:

    - **<facet>** — bar: <the standard, one sentence> — ref: <path in ref/, or none> — capture: <cmd>

Facets, and where their bar usually comes from:

- `play` — a gameplay video of the reference cut into a filmstrip, plus the
  numbers pulled from it: time to first action, actions per minute, how long a
  run lasts, how often the state changes.
- `feel` — input-to-response latency in ms, frames from press to visible change.
  Measurable, therefore strong: a free gate rather than a critic round.
- `meta` — an inventory: how many upgrades, how long to see them all, what
  carries between sessions.
- `content` — counts, from CONTRACT.md.
- `ux` — the reference's flow screen by screen: how many taps from launch to
  playing, what it explains and when.
- `audio` — a reference clip, plus counts: distinct SFX per 30 seconds, is there
  music, does it react.
- `perf` — a number: target frame rate at target complexity on the target device.
- `visual` — the screenshots. One facet of eight.

A bar has to be **openable** (a file, a URL, a recording, a number) and it should
be **out of reach** — if we can match it in two rounds it will not stop us
settling.

- **play** — bar: <standard> — ref: <path|none> — capture: <cmd>
- **feel** — bar: <standard> — ref: <path|none> — capture: <cmd>
- **meta** — bar: <standard> — ref: <path|none> — capture: <cmd>
- **content** — bar: <standard> — ref: <path|none> — capture: <cmd>
- **ux** — bar: <standard> — ref: <path|none> — capture: <cmd>
- **audio** — bar: <standard> — ref: <path|none> — capture: <cmd>
- **perf** — bar: <standard> — ref: <path|none> — capture: <cmd>
- **visual** — bar: <standard> — ref: <path|none> — capture: <cmd>
"""

HARNESS = """# Harness — frozen after stage 2

The highest-leverage thing built in this run. Without it a critic grades a
*description* of the game, and descriptions always pass.

## Stack

CHOSEN: {stack}

<Why this stack, in one sentence — and specifically whether its capture can run
with no window and no human. That is the only property that decides whether this
run can go overnight.>

CAPTURE PROVEN: no

<This line is flipped by `preflight.py`, never by hand. It runs the SESSION
command twice with one seed and checks files, metrics, determinism and the
blind-pair path. next.py warns every round while this says no, because every
unattended round past this point is a guess otherwise.>

## The five frozen commands

One per line, machine-read by preflight.py and next.py — keep the `NAME: cmd`
shape. Start SESSION from `scripts/templates/capture_web.mjs` (or `session.gd`
for Godot); see references/harness.md. Determinism matters more here than
anywhere else: fixed seed, scripted inputs, fixed duration, fixed framing.

SESSION: <one command, no window, no human — writes frames + filmstrip + metrics.json>
SCREENSHOT: <command, fixed viewport, matching the reference's framing>
FIRST SESSION: <the same session from a cold start, no saved state, no unlocks>
PERF: <command printing the frame rate at target complexity>
SOAK: <the long session, for stage 7>

The SESSION must emit both:

- **a filmstrip** — frames at a fixed interval across the fixed scenario, tiled
  into one image. A loop is visible in a filmstrip and invisible in a single
  frame. This is what goes into the blind A/B against the reference video's strip.
- **a metrics JSON** — at minimum `completed`, `duration`, `fps_mean`, `fps_min`,
  `events`. Half the lenses can be scored off numbers, and numbers are free every
  round.

Freeze all of these in stage 2 and reuse them every round. If the framing or the
scenario changes between rounds, improvement becomes indistinguishable from
reframing.
"""

ART = """# Art — frozen after stage 1, alongside the pillars

The visual bar is the ceiling of the stack, not parity with the reference —
see references/art.md, including the ceiling catalogue for this stack. The
`visual` facet is not won while the post chain is off or the signatures below
are missing from the capture.

## Direction

<One named phrase with an opinion in it — "neon-noir in the rain", not
"stylised and colourful". Test: could an artist paint a key frame from the
phrase alone and land close? Steal the identity from another medium — film,
album covers, architecture — not from the reference game.>

## Palette

<4–6 hex values with roles: dominant, secondary, one RESERVED accent that
means something (danger / interactable / reward) and appears nowhere else.
Name the forbidden colours too.>

## Light

<Where it comes from, its colour, how hard the shadows are, what fog or
atmosphere does. Light is 80% of the look — authored light on grey boxes
already reads as the game; default ambient on textured assets never does.>

## Shape language

<What silhouettes are made of, and what is deliberately absent.>

## Signature techniques (minimum three)

The things by which a screenshot of this game is recognised among a hundred
genre-mates. Concrete, from the ceiling catalogue — "wet asphalt doubles every
light source", not "moody atmosphere". One of them is the dominant; the rest
support it.

- <technique 1 — the dominant>
- <technique 2>
- <technique 3>
"""

RUBRIC = """# Rubric — frozen before the first polish round

One lens per round. next.py rotates them: it takes the lens of the current facet
that has gone unused longest, so a skipped or redone round repairs the rotation
instead of corrupting it.

Frozen before stage 6 opens, for a specific reason: a rubric written after seeing
the output is a rubric shaped by the output. From here it may only be made
**stricter**, never looser, and every edit gets a line in STATE.md saying what
changed and why. Softening it is how a run declares victory over a bar it never met.

Each lens should name the pillar it defends. A lens that defends no pillar is
grading a generic idea of quality rather than the distance to this bar.

Syntax:

    - **<facet>/<lens name>** — <the question it asks, and what to look at>

Starter set below. Adapt every line to the bar actually chosen in BARS.md before
the first polish round.

- **play/core loop** — read across the filmstrip: what is happening per frame on the bar that is not happening on ours?
- **play/challenge & pacing** — can you lose? does pressure rise and settle, or is ours flat?
- **play/feedback density** — how many things answer a single input on the bar, and how many on ours?
- **play/session shape** — start to end of one session: does it build, and is there a reason to press restart?
- **feel/impact** — does a hit, a landing, a collision read in a single frame?
- **feel/responsiveness** — frames from input to visible change, ours vs the bar's number
- **feel/weight** — does the thing being steered have mass, or does it slide on numbers?
- **feel/restraint** — does the juice stack into noise? more is a loss if the bar is calmer and reads better
- **meta/progression legibility** — can a player tell what they are working towards without being told?
- **meta/reason to return** — what does the bar leave unfinished that pulls you back tomorrow?
- **meta/economy health** — every resource: does it have both a source and a sink, and is either runaway?
- **content/variety** — is this N distinct things, or one thing renamed N times? distinct = differs from its neighbour on ≥2 variety axes (references/critics.md)
- **content/density** — how much happens per minute of the bar, and per minute of ours?
- **ux/first sixty seconds** — from launch to playing: how many taps, how much reading, how much doubt?
- **ux/hierarchy** — what does the eye hit first, and is it the same thing as on the bar?
- **ux/state completeness** — loading, empty, error, first-run: which states exist on the bar and not on ours?
- **audio/coverage** — which actions answer in sound on the bar and are silent on ours?
- **audio/mix** — is anything too loud, too quiet, or fighting the rest?
- **perf/frame rate hold** — does it hold its target through the worst moment, not the average one?
- **perf/stability** — over a long session: does anything drift, leak, or degrade?
- **visual/silhouette** — at 128px, does it read as the same kind of thing at all?
- **visual/value structure** — squint, ignore hue: are the light and dark masses arranged like the bar's?
- **visual/material & light** — do surfaces read as the same substance under the same light?
- **visual/cohesion** — one authored world, or parts assembled from different places?
- **visual/signature** — are ART.md's named techniques on screen, at full strength? would this frame be recognised among a hundred genre-mates?
- **visual/density** — layers of visual work in frame — authored light, post chain, particles, background motion, camera life: count the bar's, count ours
"""

BACKLOG = """# Backlog

Every unit of work, tagged with the stage that owns it. next.py hands out the
first unchecked item belonging to the current stage, so this file is what keeps a
night from inventing work.

    - [ ] stage: <N> — facet: <facet> — <what to build, one line>
    - [ ] stage: <N> — facet: <facet> — refactor: <one seam, one round's worth>

Lines whose work starts with `refactor:` are handed out **before** feature
lines, wherever they sit in the file — architecture debt is paid first
(references/code.md). The architecture audit and ARCH CHECK DUE both empty
into this file as `refactor:` lines.

It does not empty while the contract is open. When it runs dry on the current
stage but the stage is not closed, that is the signal to decompose the stage's
remaining gates into items rather than to move on.

- [ ] stage: 2 — facet: perf — build the scripted session and prove it runs headless
"""

STATE = """# gamemaker run — {slug}

Read this first on every invocation. It is the run's memory: everything else in
context can be cleared between firings and the run still resumes from here.

AMBITION: {ambition}
REFERENCE: {reference}
SCALE: {scale}

## Validation question (answered at stage 3)

<Falsifiable, and both halves matter: "Does a player starting from nothing
experience <the core fantasy> within <N> minutes, without being told how — and
can one such loop be built at representative quality?" Write it before building
the slice. A question written afterwards is shaped by what got built.>

VERDICT: <PROCEED | PIVOT | KILL — filled at the end of stage 3>

AUTOCOMMIT: yes

## Autonomy rules

{budget_line}- Rounds per firing: 3, then stop, so context never accumulates.
- Never ask a question after stage 0. If a decision is needed, take the option
  closest to the bar, write it in DECISIONS.md, and continue.
- A round's unit of work changes something the player sees or plays. Harness,
  test and tooling work is overhead between units, never the unit itself —
  fixing a regression is the one exception. next.py flags a NO-OP STREAK.
- A failing gate gets one repair round per firing; after 3 failures running,
  quarantine it — `BLOCKED: quarantined — <why>` plus a line in open_gaps.md —
  and keep building. Grinding one gate is how a firing gets spent on tests.
- Contract lines and ladder gates are never deleted, only ticked or BLOCKED.

## Ledger
"""

DECISIONS = """# Decisions taken without asking

One line each, so the morning review can see what was guessed, when, and on what
basis. A night run that produced no decisions here either had a very clear brief
or was not paying attention.

    <date> — stage <N> — <the decision> — <why this option was closest to the bar>

"""

OPEN_GAPS = """# Open gaps

The queue. Everything noticed during a round that was not that round's single
target lands here, so the round stays one change wide and attribution survives.

The design holism checklist (references/design.md) empties into this file too:
its findings are gaps, not blockers.

Prefix a line with `BLOCKED:` when a gap genuinely cannot be closed here — a
missing asset, a tool that will not run — so the run moves on instead of grinding.

"""


def write_if_absent(path: Path, body: str, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(path.name)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    created.append(path.name)


def ensure_git(run: Path) -> str:
    """A repo is what makes rounds reviewable: reveal.py commits each one, so the
    morning-after review is `git log` instead of archaeology."""
    try:
        subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       cwd=run.parent, capture_output=True, text=True, check=True)
        return ""
    except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
        pass
    root = run.resolve().parent.parent
    try:
        subprocess.run(["git", "init"], cwd=root, capture_output=True, text=True, check=True)
        return str(root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def base_allowlist(run: Path) -> str:
    """Seed the project's permission allowlist: a permission prompt at round 12
    kills an unattended firing as surely as a broken capture. preflight.py adds
    the frozen harness commands to this once they are proven."""
    root = run.resolve().parent.parent
    here = Path(__file__).resolve().parent
    rules = [f"Bash(python3 {here}/*:*)",
             "Bash(git add:*)", "Bash(git commit:*)", "Bash(git branch:*)",
             "Bash(git log:*)", "Bash(git diff:*)", "Bash(git status:*)"]
    sfile = root / ".claude" / "settings.local.json"
    try:
        settings = json.loads(sfile.read_text()) if sfile.is_file() else {}
    except json.JSONDecodeError:
        return ""
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    added = [r for r in rules if r not in allow]
    if not added:
        return ""
    allow.extend(added)
    sfile.parent.mkdir(parents=True, exist_ok=True)
    sfile.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    return str(sfile)


def gitignore(run: Path) -> str:
    """Keep run state out of the repo unless the user wants it committed."""
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             cwd=run.parent, capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
        return ""
    root = Path(top.stdout.strip())
    gi = root / ".gitignore"
    line = ".gamemaker/"
    if gi.is_file() and line in gi.read_text(errors="replace"):
        return ""
    existing = gi.read_text(errors="replace") if gi.is_file() else ""
    with gi.open("a") as fh:
        fh.write(("" if not existing or existing.endswith("\n") else "\n") + line + "\n")
    return str(gi)


def main() -> int:
    ap = argparse.ArgumentParser(description="Create a gamemaker run skeleton")
    ap.add_argument("run", help="run directory, e.g. .gamemaker/<slug>")
    ap.add_argument("--ambition", required=True,
                    help="the user's own words for what they want, verbatim")
    ap.add_argument("--scale", required=True, choices=["full", "slice"],
                    help="full = a whole game, contract derived from the reference title; "
                         "slice = 3-5 polished minutes and no content volume. Required on "
                         "purpose: a forgotten flag is how an ambitious ask silently becomes "
                         "a demo.")
    ap.add_argument("--reference", default="",
                    help="the commercial title being chased — the source of the contract's numbers")
    ap.add_argument("--stack", default="", help="engine or stack, if already decided")
    ap.add_argument("--platform", default="", help="target platform")
    ap.add_argument("--budget", type=int, default=0, help="round budget to record in STATE.md")
    args = ap.parse_args()

    run = Path(args.run)
    (run / "rounds").mkdir(parents=True, exist_ok=True)
    (run / "ref").mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    skipped: list[str] = []

    skill_root = Path(__file__).resolve().parent.parent
    ladder_body = LADDER.replace("<skill>", str(skill_root)).replace("<run>", str(run))
    write_if_absent(run / "LADDER.md", ladder_body, created, skipped)
    write_if_absent(run / "BRIEF.md", BRIEF.format(
        ambition=args.ambition,
        reference=args.reference or "<TODO: the commercial title this is measured against>",
        scale=args.scale,
        stack=args.stack or "<TODO: decided in stage 2, and only if its capture runs headless>",
        platform=args.platform or "<TODO: where this runs>",
    ), created, skipped)
    write_if_absent(run / "CONTRACT.md", CONTRACT, created, skipped)
    write_if_absent(run / "PILLARS.md", PILLARS, created, skipped)
    write_if_absent(run / "DESIGN.md", DESIGN, created, skipped)
    write_if_absent(run / "ART.md", ART, created, skipped)
    write_if_absent(run / "BARS.md", BARS, created, skipped)
    write_if_absent(run / "HARNESS.md", HARNESS.format(
        stack=args.stack or "<TODO>"), created, skipped)
    write_if_absent(run / "RUBRIC.md", RUBRIC, created, skipped)
    write_if_absent(run / "BACKLOG.md", BACKLOG, created, skipped)
    write_if_absent(run / "DECISIONS.md", DECISIONS, created, skipped)
    write_if_absent(run / "open_gaps.md", OPEN_GAPS, created, skipped)

    budget_line = (f"- Budget: stop after round {args.budget}. This cap is what protects the "
                   f"account limit.\n" if args.budget else
                   "- Budget: <N rounds, or 'until the user stops it'>\n")
    write_if_absent(run / "STATE.md", STATE.format(
        slug=run.name, ambition=args.ambition,
        reference=args.reference or "<TODO>", scale=args.scale,
        budget_line=budget_line), created, skipped)

    inited = ensure_git(run)
    gi = gitignore(run)
    allow = base_allowlist(run)

    print(f"run skeleton: {run}")
    if created:
        print(f"  created: {', '.join(created)}")
    if skipped:
        print(f"  left alone (already existed): {', '.join(skipped)}")
    if inited:
        print(f"  git repo initialised in {inited} — reveal.py commits every round into it")
    if gi:
        print(f"  added .gamemaker/ to {gi}")
    if allow:
        print(f"  seeded permission allowlist: {allow} (preflight.py adds the harness commands)")

    print(f"\nScale: {args.scale}", end="")
    if args.scale == "slice":
        print(" — no content volume is promised. If the ambition named a real game,")
        print("  this is the wrong scale and now is the only cheap moment to change it.")
    else:
        print(" — the contract must be filled with numbers from the reference title")
        print("  before stage 0 can close. Inventory the real game first, then commit.")

    print("\nStage 0 is open. Before it closes:")
    print("  - BRIEF.md: session shape, the one-sentence core activity, how the scale was read")
    if not args.reference:
        print("  - BRIEF.md: the reference title — the contract has nowhere to get its numbers without it")
    print("  - CONTRACT.md: the reference inventory first, then the targets, each with a `count:` command")
    print(f"\nThen: python3 {Path(__file__).resolve().parent / 'next.py'} {run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
