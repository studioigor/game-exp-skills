---
name: gamemaker
description: "Производственная лестница от одной строчки амбиции до готовой игры — «сделай клон Need for Speed» приводит к настоящей игре, а не к красивому скриншоту или демке на сорок секунд. Семь ступеней с воротами (бриф → дизайн → harness → вертикальный срез → системы → контент → полировка → релиз), контракт объёма в числах, который не даёт объявить победу на одной трассе, столпы и анти-столпы, чек-лист холизма геймдизайна, арт-дирекция с планкой «максимум стека + фирменные приёмы» вместо серого минимума, архитектурный стандарт с правилом «рефакторинг раньше фич», механический preflight harness'а, слепое A/B против планки по каждому фасету и три типа раунда (BUILD / FILL / POLISH). Всё состояние на диске — прогон переживает /clear, каждое включение независимо, возобновляется из состояния на диске; ночной запуск возможен только при наличии поддерживаемого планировщика. Работает от трёх входов: одна фраза («клон NFS», «игра про выживание в метро»), подробный GDD/ТЗ, или скриншоты-референсы. Использовать ВСЕГДА, когда пользователь просит СДЕЛАТЬ ИГРУ целиком: «сделай клон X», «сделай ААА игру», «сделай игру про Y», «вот ТЗ на игру — реализуй», «вот скриншоты, сделай такую игру», «доведи мою игру до релиза», «собери полноценную игру, не прототип», «запусти на ночь делать игру». НЕ применять, когда игра уже есть и нужно улучшить одну грань без стройки (это gauntlet-loop), когда нужен аудит существующей игры, для генерации одного ассета, спрайтлиста или иконки, и для не-игровых продуктов."
---

## OpenAI runtime adaptation

Apply these runtime bindings throughout this packaged skill and its references.
They replace edition-specific tool, scheduling and installation requirements;
preserve the production ladder, quality bars, round budgets and measured QA.

- Resolve `<skill>` to the directory containing this SKILL.md. Run bundled scripts
  through the current environment's file and shell capabilities. Never assume a
  Claude installation path or launch a nested Claude/Codex CLI.
- Ask with the current surface's structured question tool when available;
  otherwise ask briefly in chat. Treat `AskUserQuestion` and slash invocations as
  descriptions of intent, not required API names or executable commands.
- Use available research, image viewing, editing and live preview capabilities.
  Generate raster art with the session's built-in image generation capability.
  If required execution, capture or image generation is unavailable, identify
  the blocker, preserve state and continue only work that does not depend on it.
  Never claim a runnable build, successful capture or passed QA without evidence.
- Delegate only when subagents are supported. Otherwise perform the same rubric
  as labelled self-review; do not represent it as independent criticism.
- Keep project state on disk. Goal APIs, `CronCreate` and `/loop` are optional
  lifecycle mechanisms. Use them only when supported and the user explicitly
  requests persistent or scheduled execution. Merely invoking this skill does
  not authorize scheduling. Without that capability, perform a bounded batch
  in this turn, checkpoint state, and report how to resume. Never promise work
  after the turn ends. Skip unavailable Goal calls, including completion calls.
- For scheduled execution, preserve the agreed budget, stop conditions and
  preflight gates. Do not silently replace an unrelated active task or Goal.
- Install only tooling appropriate to the selected engine and available runtime.
  Claude-specific project instruction files or agent templates are reference
  material on other surfaces, not automatically active agents or instructions.
- Respect user authorization and environment policies. Plugin installation alone
  does not authorize publishing, payment, sign-in or changes to external systems.

# gamemaker — the production ladder

A method for getting from "make me a clone of Need for Speed" to a game somebody
can actually play for an evening.

The ambition is the easy part. What kills a solo AI-built game is always one of
three things, and this skill is built around refusing each of them:

1. **Polishing something that was never designed.** "Clone of NFS" is an
   ambition, not a design. Between them sit pillars, a core loop at three scales,
   a systems list, an economy, a difficulty philosophy. Skip that and every later
   round improves whatever happened to be in front of it.
2. **Polishing something that is 40% built.** A polish loop makes an existing
   thing better one gap at a time. Applied to a 40%-complete game it produces a
   beautifully polished 40%, and the missing 60% never surfaces as a gap, because
   the critic only ever sees what the capture captured.
3. **Declaring victory on one level.** One gorgeous track will pass every quality
   lens there is. It is still a demo.

So the run climbs a **ladder** of seven stages with gates between them, and the
gates are enforced by a script rather than by good intentions. Inside every stage
the engine is the same cheap round — free gates, capture, one change, log — and
only the definition of "gap" changes.

Everything lives on disk. A firing reads `STATE.md`, asks `next.py` what to do,
does two or three rounds, and stops. That is what makes the run survive `/clear`,
makes each firing independent, and lets it grind for several nights.

## Invocation

- `/gamemaker <ambition>` — start a run. The ambition can be one sentence, a GDD,
  a folder of screenshots, or an existing half-built game.
- `/gamemaker continue [slug]` — resume. Always resumable, always cheap.
- Unattended: `/loop 25m /gamemaker continue <slug>` — each firing does a few
  rounds and stops, so context never bloats across a long grind.

## Run layout

```
.gamemaker/<slug>/
  LADDER.md       the seven stages and their gates — the spine
  BRIEF.md        ambition · reference title · scale · stack · platform — frozen after stage 0
  CONTRACT.md     the scope contract, in numbers — never trimmed, only ticked or BLOCKED
  PILLARS.md      3–5 falsifiable pillars + anti-pillars — frozen after stage 1
  DESIGN.md       core fantasy · the loop at three scales · systems · difficulty · economy
  ART.md          direction · palette · light · 3+ signature techniques — frozen after stage 1
  HARNESS.md      the frozen capture commands, and whether they are proven
  BARS.md         one bar per facet, with its reference and its capture
  RUBRIC.md       the lenses, per facet — frozen before the first polish round
  BACKLOG.md      units of work, tagged by stage
  STATE.md        the ledger — READ THIS FIRST on every invocation
  open_gaps.md    the queue: noticed, but not this round
  DECISIONS.md    what was decided without asking, and why
  ref/            reference assets, per facet
  rounds/NN/      artifact · ab/{A,B,key.json} · verdict.md · outcome.json
  progress.html   regenerated every round
```

`init.py` writes all of it in the exact shapes the other scripts parse. Hand-writing
these is where runs break: a `LADDER.md` whose headers do not match
`## Stage N — NAME` leaves `next.py` unable to find the stage, and that shows up at
3am rather than now.

## Phase 0 — resume before anything else

If `.gamemaker/*/STATE.md` exists, read it and run `next.py`. Do not re-derive the
brief, the pillars or the contract — that is the most expensive mistake available
here, and it quietly resets the standard mid-run.

One thing is worth re-reading on resume, because no later stage can repair it:
`next.py` prints the ambition and the scale together. If the ambition names a real
game and the scale says `slice`, the run is building a demo of something that was
asked for as a game. Fix it now or never.

---

# Stage 0 — BRIEF

**The only stage that may talk to the user.** They came to hand over an ambition
and get a game, not to configure a pipeline. One pass of questions, at most three,
then the run goes quiet until it has something to show.

Never ask anything if the run is unattended — launched under `/loop`, or the
prompt says so. Take the reading closest to the ambition, write it in
`DECISIONS.md`, continue. A question asked at midnight blocks until morning.

Four things get decided:

**1. The reference title.** What commercial game is this measured against? It is
the source of every number in the contract and most of the bars. "Clone of NFS"
names it outright; "a game about surviving in the metro" needs one chosen and
stated. Without it the run has no standard except its own taste, and taste drifts
towards whatever is easy.

**2. The scale.** `full` or `slice`, and it is a real decision:

- **`full`** — the whole game. The contract is derived from the reference title's
  actual inventory. This is what a named commercial title asks for, and it is the
  default reading of an ambitious sentence.
- **`slice`** — 3–5 polished minutes and no content volume. Correct only when the
  user said prototype, demo, or proof of concept.

When the wording is ambitious and you are about to pick `slice`, that is almost
always the run flinching rather than the user asking for less. Pick `full`.

**3. The scope contract.** Inventory the reference title *first* — how many
tracks, cars, enemies, weapons, levels, hours — and write that inventory into
`CONTRACT.md` before choosing a single target. Then commit to targets with a
`count:` command each.

The contract is the anti-lowball device and it has exactly three rules:

- numbers come from the reference, not from what fits in one night;
- a line may be marked `BLOCKED: <why>` but **never deleted** — `contract.py`
  keeps a baseline and reports lines that disappear;
- the run does not report done while a line is open.

Aim for 6–10 lines. Prefer commands that count real things (`ls data/tracks/*.json
| wc -l`, a JSON array length, a grep) — a counted line is verified free every
round, a `manual:` line is a promise nobody checks.

**4. The platform and the session shape.** Where it runs, and what one sitting
looks like. Both feed the contract and the ship gates.

```bash
python3 <skill>/scripts/init.py .gamemaker/<slug> \
  --ambition "<the user's own words, verbatim>" \
  --scale full --reference "<the commercial title>" --budget 200
```

## When the input is a GDD or ТЗ

A spec handed in is a **goal, not a bar**. It says what to build and nothing about
how good it has to be; graded against it, a critic scores "implemented / not
implemented" and the run stops the moment the checklist is full. Split it:

- **ambiguities → resolved now**, in the one pass with the user. An unresolved
  ambiguity becomes a 3am guess baked into forty rounds.
- **requirements → `CONTRACT.md` and the ladder's gates**, machine-checkable
  wherever possible.
- **sections → `DESIGN.md` systems and `BACKLOG.md` items.** A spec has usually
  done the decomposition already; adopt it rather than inventing a rival one.
- **the bar still comes from outside the spec** — a real game doing the same job.

## When the input is screenshots

Screenshots are the bar for **one facet out of eight**. They say what a game looks
like and nothing at all about what it plays like, and what it plays like is most
of what the ambition meant.

Taking them as the whole bar is the single most common way this kind of run
delivers the wrong thing, and every step of the slide looks correct from inside:
the screenshots are the only inspectable thing → so they become the bar → a
screenshot bar can only be compared against a screenshot → so the artifact becomes
a frame → a frame decomposes into regions → so the work becomes city, road, car,
HUD → forty rounds later there is a stunning wet neon street that nobody can
drive. The error is at step one and it cannot be repaired later.

So: copy them into `ref/` as the `visual` bar, and go find the other seven
(`references/bars.md`). Also settle explicitly whether they are the bar (someone
else's game — "make it like this") or the starting state (the user's own — "here's
mine, fix it"). If they are the starting state, the bar still has to come from
outside, or the run tops out at slightly better than what it was handed.

## When the input is an existing game

"Доведи мою игру до релиза" enters the same ladder — through an audit, not
through hope:

1. **Architecture audit first** — the audit section of `references/code.md`:
   map the layout against the standard, run the greps, find the god object,
   check the seams the run depends on (headless session, scriptable input,
   save versioning). Verdict in `DECISIONS.md`: **sound** / **fix the seams**
   / **restructure**.
2. **Every finding becomes a `refactor:` line in `BACKLOG.md`** — and `next.py`
   hands those out **before any feature**. On a *restructure* verdict the first
   firings build no features at all, and that is correct: every feature built
   on a bad seam is built twice.
3. Gates that are already true get ticked **with real `check:` commands**, not
   on faith — a gate ticked on faith is the move that breaks the ladder.
4. `DESIGN.md` and `ART.md` are reverse-derived from the game and confirmed
   with the user in the one stage-0 pass; ambiguity resolved now, like a GDD's.
5. The ladder enters at the first stage that is not closed. The bar still comes
   from outside (`references/bars.md`) — a run whose standard is its own
   starting state can only tie with itself.

---

# Stage 1 — DESIGN

What this game **is**, decided before anything is built, because a design derived
after the fact is a rationalisation of whatever got built.

Read `references/design.md` in full here — it carries the craft this stage runs
on, including genre blueprints to start each output from. The five outputs:

**Pillars and anti-pillars** (`PILLARS.md`) — three to five principles that are
*falsifiable* ("combat rewards patience over aggression", not "fun combat"),
*constraining* (if it never forces a no, it is decoration), *cross-departmental*,
and *memorable*. Anti-pillars say what this game deliberately will not do; they
are what a 3am decision gets checked against.

**The core loop at three scales** (`DESIGN.md`) — 30 seconds, 5–15 minutes, one
session. Each fails differently and each earns its own work later. If the 30-second
action is not satisfying on its own, nothing built on top rescues it.

**The systems list** — every system tagged `tier: mvp` or `tier: full`, with the
pillar it serves and a `check:`. A system that serves no pillar is scope creep
with a nice name: cut it or add the pillar it implies.

**Difficulty philosophy and economy** — which of the four difficulty philosophies
this game takes, what its challenge axes are, and every resource with its faucets
and its sinks.

**Art direction** (`ART.md`) — read `references/art.md`. A named direction with
an opinion in it, a palette in hex, the light, and **at least three signature
techniques** by which a screenshot of this game is recognised among a hundred
genre-mates. The visual bar this sets is the **ceiling of the stack**, not
parity with the reference — a run that skips this ships the flat-lit default
look that every AI-built game ships, and no polish round can retrofit an
identity that was never chosen.

Then run the **holism checklist** (`references/design.md`) and put what it finds
into `open_gaps.md`. Eight checks — competing progression loops, attention budget,
dominant strategy, faucets and sinks, curve mismatch, pillar drift, fantasy
coherence, onboarding complexity budget — and every one of them is invisible to
every lens in the rubric, because no single capture shows them. Cheap now,
structural later.

---

# Stage 2 — HARNESS

The highest-leverage thing built in the whole run. Without a capture, the critic
grades a *description* of the game, and descriptions always pass.

Two things get decided and one gets proven.

**The stack.** This skill is engine-agnostic, but agnostic survives exactly as far
as the capture does: a stack whose session cannot be recorded without a human
cannot be run overnight, and finding that out at 3am costs a night. So choose in
this order unless the user has already decided — web (Three.js, canvas; captured
headless with Playwright) → Godot (`--headless`) → anything else.

If the user has fixed a stack whose capture cannot be proven — Unity on macOS is
the usual case, between the licence and the window — **say so plainly** and offer
the honest alternative: the loop runs at their pace, they drop a recording in each
round, and there is no night mode. Pretending otherwise wastes the night.

**The bars, per facet** (`BARS.md`). `play`, `feel`, `meta`, `content`, `ux`,
`audio`, `perf`, `visual`. Most of them are numbers, which makes them free gates
rather than critic rounds. `references/bars.md` says where each one comes from.

**The proof.** Stage 2 does not close on a claim. Build the session from the
bundled template (`scripts/templates/capture_web.mjs`, or `session.gd` for
Godot — `references/harness.md`), so that one command writes both:

- **a filmstrip**: frames at a fixed interval across a fixed scenario, fixed seed,
  scripted inputs, fixed duration, tiled into one image. A loop is visible in a
  filmstrip and invisible in a single frame. This is what goes into the blind A/B.
- **a metrics JSON**: at minimum `completed`, `duration`, `fps_mean`, `fps_min`,
  `events`. Half the lenses can be scored off numbers, and numbers are free.

Then prove it mechanically — `CAPTURE PROVEN: yes` is written by a script, not
by hand:

```bash
python3 <skill>/scripts/preflight.py .gamemaker/<slug>
```

It runs the session twice on one seed (files, metrics, determinism), checks the
screenshot and the blind-pair path, flips the flag on a full pass, and adds the
proven commands to the project's permission allowlist. `next.py` warns every
round until this passes, because every unattended round past this point is a
guess otherwise.

Freeze all the capture commands here and reuse them every round. If the framing or
the scenario changes between rounds, improvement becomes indistinguishable from
reframing.

---

# Stage 3 — SLICE

The whole game, end to end, ugly. Complete beats gorgeous, and it is the only
thing the rest of the run can operate on.

**Before the first line of code, read `references/code.md` and build the
skeleton to it** — simulation/render/state/ui/data separation, one seeded RNG,
tuning numbers in data files. A forty-round run compounds whatever structure
round 1 chose; the standard costs an hour here and pays it back every round,
and stage 4's grep gates assume it.

Write the **validation question** into `STATE.md` before building, because a
question written afterwards is shaped by what got built. It is falsifiable and it
has two halves that both matter:

> Does a player starting from nothing experience *\<the core fantasy\>* within
> *\<N\>* minutes, without being told how — and can one such loop be built at
> representative quality?

Target **3–5 minutes of continuous play**. Longer is not more convincing; it is
just more to build at a quality that has not been proven yet.

**Cut scope, not quality.** A slice that looks nothing like the intended game
cannot validate anything. If it will not fit, remove content, never craft.

**Sunk-cost checkpoint.** If the full start → challenge → resolution cycle is not
demonstrable when planned, stop and reassess. Either the scope was wrong or an
architectural assumption is. Surfacing that beats iterating past it.

Then the **verdict**, written into `STATE.md`:

- **PROCEED** — the loop works. The ladder continues.
- **PIVOT** — the thing is wrong at the root and polish will not save it. Go back
  to stage 1, change the design, build the slice again. This is a legitimate
  stop and it is *not* the "good enough" this method exists to refuse — it is the
  opposite. It is available **only here**, before the polish stages; past stage 3
  the run does not get to give up on hard gaps.
- **KILL** — the ambition cannot be met with this stack, in this environment. Say
  so, plainly, with the evidence. Rare, and worth more than forty rounds of
  pretending.

---

# Stage 4 — SYSTEMS

Everything tagged `tier: mvp` in `DESIGN.md`, built and checked. `next.py` reads
the list and hands them out one at a time.

Each system closes with a `check:` that runs. That check then joins the free gates
and re-runs every round for the rest of the run, which is what catches round 30's
lighting work quietly breaking the fail state round 6 built.

**Every defect closed adds a check.** When a round fixes a bug, it writes the check
that would have caught it. This is the cheapest compounding thing in the whole run:
by stage 6 the free gates are catching regressions that no lens would ever look at.

---

# Stage 5 — CONTENT

The volume. This is the stage solo projects skip and it is precisely what separates
a game from a demo — and it is the cheapest stage per round, because content rounds
are counted rather than judged.

Work the open lines of `CONTRACT.md`. `contract.py` runs the counts and prints the
standing; it is also this stage's exit gate.

The one quality bar that applies here: **variety, not repetition.** Eight tracks
that are the same track with different textures satisfy the count and fail the
purpose. Distinct means differing from the neighbour on **at least two variety
axes** — layout, dominant mechanic or hazard, palette/mood, pacing shape,
optimal strategy (`references/critics.md`, the content section). If a unit
cannot be told from its neighbour in the filmstrip, it did not count.

---

# Stage 6 — POLISH

Now, and only now, the classic gauntlet round: each round takes **one facet** under
**one lens** and closes **exactly one gap**.

`RUBRIC.md` is frozen before the first polish round and from then on may only be
made **stricter**, never looser; every edit gets a line in `STATE.md`. Softening it
is how a run declares victory over a bar it never met.

`next.py` rotates: it takes the facet that has gone longest without a round, then
that facet's least-recently-used lens, so a skipped or redone round repairs the
rotation instead of corrupting it.

A facet is **won** when our side takes every one of its lenses across one clean
rotation. A single win is noise; a rotation is a result.

---

# Stage 7 — SHIP

Read `references/ship.md`. The gates that separate "works on my machine" from
something a stranger can play:

- a **soak session** at the target length — leaks, frame-time drift, state
  accumulation, content exhaustion, fun fatigue. None of these appear in a
  30-second strip, and all of them appear to a player on their second evening.
- nothing shipped that is placeholder, debug, lorem or a console log;
- every action answers in sound and motion;
- the platform's own requirements (store SDK, ratings, store card assets —
  see `references/ship.md`).

---

# The round

Every round has the same shape whatever its type. Ask what it is — one command
instead of re-deriving it from nine files:

```bash
python3 <skill>/scripts/next.py .gamemaker/<slug>
```

It prints the stage, what is blocking it, the round number and type, the facet,
the unit of work, the capture command, the free gates, the contract standing, the
budget, and any warning worth acting on. If it says `NOT READY`, finish that stage
rather than improvising — it means the ladder is protecting something.

**a. Free gates.** Build, typecheck, lint, tests, the capture itself, every `check:`
from every closed stage. Broken output gets fixed without spending a critic — there
is no point judging a render that failed to render. A gate that used to pass and now
does not is a **regression**, and it outranks whatever this round was going to do.

**b. Capture** into `rounds/NN/` with the frozen command.

**c. The work**, which depends on the type:

| Type | Stages | What the gap is | How it is judged |
|---|---|---|---|
| **BUILD** | 3, 4, 7 | a missing capability | the gates decide; no critic, no pair |
| **FILL** | 5 | a missing count | `contract.py` counts it |
| **POLISH** | 6 | a quality shortfall against this facet's bar | blind A/B, one lens, one gap |

A **POLISH** round additionally:

- **Blind pair** — run the `ab.py` line `next.py` printed. It normalises format and
  size, shuffles the sides into `A` and `B`, and writes the key. Do not read
  `key.json`, and do not `ls -l` the pair — file sizes are a tell.
- **Critic pass** — read **only** `RUBRIC.md`, `open_gaps.md`, this facet's
  section of `references/critics.md` (the discipline's own eyes — what an art
  director or sound designer looks at first), and the two sides.
  Deliberately do *not* re-read the code just written or the reasoning behind it.
  The artifact is what is being judged; the code is where rationalisation lives,
  and "but I did that on purpose" is exactly the thought a separate critic would
  never have.
- **Default to the bar winning.** Only call ours the winner when you can point at
  the specific thing that makes it win under this lens.
- Name **exactly one** gap — the biggest. Not a list; a list becomes a shotgun
  patch and then nothing tells you which change moved the needle. Everything else
  goes to `open_gaps.md`.

**d. Verdict**, ≤12 lines. It exists to steer the next round, not to document the run.

```markdown
# Round NN — POLISH — facet: play — lens: core loop

WINNER: A
GAP: <the single biggest gap, as an observable difference>
WHY: <2–3 lines in rubric terms>
FIX: <the concrete change to make this round>
```

For BUILD, FILL and SHIP rounds it is shorter, and `reveal.py` insists on both lines:

```markdown
# Round NN — BUILD — facet: play

DID: <the one thing built>
GATES: pass
```

**e. Log** — `python3 <skill>/scripts/reveal.py .gamemaker/<slug>/rounds/NN`

One command for every round type. On a polish round it enforces commit-then-reveal
and will not open the key until the verdict carries a `WINNER:` and a single `GAP:`.
Then it writes `outcome.json` and appends the ledger row itself.

**f. Close the gap.** That one thing, nothing else, however tempting and nearby —
that is what the queue is for.

**g. Redraw** — `python3 <skill>/scripts/progress.py .gamemaker/<slug>`

Then go again. Do not narrate rounds to the user in prose; `progress.html` and
`STATE.md` are the report and they cost nothing.

---

## Running it unattended

Stages 0–2 are done **with the user reachable**. Everything after is loopable —
at any hour, for as many hours as the user wants: the run is built to grind
whether or not anyone is watching, and "unattended" is a property of the firing,
not of the clock.

The rules the firings obey live in `STATE.md` (the Autonomy rules section
init.py wrote), not in the loop prompt, because `STATE.md` is what every firing
reads first and it survives a cleared context: rounds per firing, never-ask,
the gate-repair budget, the no-op rule.

The launch checklist, in order:

```bash
python3 <skill>/scripts/preflight.py .gamemaker/<slug>  # proves the harness, seeds the allowlist
python3 <skill>/scripts/next.py .gamemaker/<slug>      # must print a real round, no NOT READY
# do one full round by hand: gates → capture → work → reveal. It must run prompt-free.
caffeinate -i &                                # only if the machine may sleep
/loop 25m /gamemaker continue <slug>
```

A fixed interval beats self-pacing here: predictable spend, and it cannot decide
to nap.

Each firing is the same boring script: read `STATE.md`, run `next.py`, do two or
three rounds, stop. Stopping early is correct — the next firing picks up from
disk with a clean context, which is the cheapest critic available. If `next.py`
reports a stop condition or `NOT READY` that needs a human: send a
PushNotification with the reason (when the tool is available), leave a line in
`STATE.md`, and stop. Never invent work to fill a firing.

Three things actually kill unattended runs, in order of frequency: **a
permission prompt** (the loop stops dead at the first one — `init.py` and
`preflight.py` seed `.claude/settings.local.json` with the run's own commands;
the hand-run round above is the proof it worked, or use bypass mode for the
window), **the machine sleeping** (`caffeinate -i`), and **grinding one failing
gate for hours** (the quarantine rule: one repair round per firing, `BLOCKED:
quarantined` after three — `next.py` watches for it).

Review needs no morning and no ceremony: `reveal.py` commits every round, so
the diff trail is `git log`, and the Activity table in `progress.html` shows
each firing's rounds, wins, gate failures and no-op count at a glance.

## Staying inside the limits

The constraint that shapes the whole design. Each rule earns its place:

- **One critic per round, never a fleet.** A round is small; an agent is not.
- **Most rounds spend no critic at all.** BUILD and FILL rounds are decided by
  gates and counts. On a full run they are the large majority.
- **One gap per round.** Keeps rounds small and makes attribution possible.
- **Free gates before paid critique.** Never spend a critic on broken output.
- **The critic's read-set is fixed and small** — rubric, open gaps, two artifacts.
  Never the round history: `STATE.md` and `progress.html` exist for the human.
- **Shrink before viewing.** `ab.py --shrink 1000` by default; a 4K screenshot
  costs several times as much to look at and adds nothing at any of these lenses.
- **Scripts do all the bookkeeping.** Never hand-write the ledger, the progress
  page or the next round's parameters — that is pure token spend on work a script
  does deterministically and does not get wrong on round 134.
- **Clear between rounds on long runs.** The run reloads from `STATE.md`, so
  `/compact` or `/clear` at a stage or lens boundary is both the cheapest context
  and the closest thing to a genuinely fresh critic. This is a feature.

## Failure modes

| Symptom | What is actually wrong | Fix |
|---|---|---|
| A gorgeous screenshot and no game | the screenshots were taken as the whole bar | they are the `visual` facet; go get the other seven — `references/bars.md` |
| Beautiful vertical slice, then nothing | the run treated stage 3 as the finish line | the contract is the finish line; stage 5 is where a game stops being a demo |
| Three tracks and a menu, reported as done | the contract was written from what fits in a night | numbers come from the reference inventory; `contract.py` reports deletions |
| Rounds stop changing anything | the gap is phrased as a feeling, not an observable difference | rewrite it as "the bar has X where ours has Y" — `next.py` flags this as STALL |
| Every round says OURS WINS | self-recognition plus a soft rubric | tighten the rubric, raise the bar, re-read the reveal's own warning |
| The rubric got easier over the run | goalpost drift | stricter-only; log every edit in `STATE.md` |
| Systems all work, the game is boring | the holism checks never ran | competing loops, dominant strategy, dead economy — `references/design.md` |
| Content count met, still feels empty | eight copies of one thing | variety is stage 5's other gate; if it is indistinguishable in the strip it did not count |
| Fixed five things, it got worse | shotgun patching | one gap per round, the rest to the queue |
| Cannot tell if anything improved | the capture changed between rounds | freeze it in stage 2, never touch it again |
| Unattended run did nothing for hours | a permission prompt, or the harness was never proven | `preflight.py`; the seeded allowlist; one hand-run round before the loop |
| Hours of rounds, the game never changed | the run polished its own scaffolding — tests, harness, tooling | `next.py` flags NO-OP STREAK; a unit changes what the player sees or plays |
| One gate failing all night | regression-outranks with no ceiling | quarantine: one repair round per firing, `BLOCKED: quarantined` after 3 |
| Round 30 code is a swamp | architecture drift no lens ever sees | ARCH CHECK DUE → `refactor:` lines, and they are handed out first |
| Looks fine, looks like everything else | the visual bar was read as parity with the reference | the bar is the stack's ceiling + ART.md signatures — `references/art.md` |
| Everything works, nobody can start it | the first sixty seconds were never a facet | `ux/first sixty seconds` is a lens; the first-session capture is what reads it |

## Bundled files

- `scripts/init.py` — the run skeleton, in the shapes the other scripts parse;
  also seeds the git repo and the permission allowlist.
- `scripts/next.py` — the spine: stage, gates, round type, facet, capture,
  budget, and the guard rails (STALL, NO-OP STREAK, GATE QUARANTINE, ARCH CHECK).
- `scripts/preflight.py` — proves the harness mechanically and flips
  `CAPTURE PROVEN` itself. Stage 2's exit, and the first line of the launch checklist.
- `scripts/contract.py` — counts what exists against what was promised.
- `scripts/ab.py` — blind pair: normalises, shuffles, writes the key.
- `scripts/reveal.py` — closes any round; enforces commit-then-reveal on polish;
  commits the round and records what actually changed.
- `scripts/progress.py` — the self-contained live progress page, with the
  per-firing Activity table.
- `scripts/templates/capture_web.mjs`, `scripts/templates/session.gd` — working
  capture starting points for web and Godot. Copy and adapt in stage 2.
- `references/design.md` — pillars, the holism checklist, nested loops, difficulty,
  economy, genre blueprints. Read in stage 1.
- `references/art.md` — the visual ceiling per stack, the creative method, what
  ART.md must contain. Stage 1, and every visual round.
- `references/code.md` — the architecture standard, the grep gates, the audit,
  refactor-first. Read at stage 3 before the first line of code.
- `references/harness.md` — building and proving the capture, per stack. Stage 2.
- `references/bars.md` — where each facet's bar comes from, typical numbers by
  genre, the video-extraction protocol, the juice checklist. Stage 2.
- `references/critics.md` — one professional's eyes per facet; read the round's
  facet before every polish verdict. Content's variety axes live here too.
- `references/ship.md` — soak, perf budgets, save compatibility, placeholder
  sweep, platform requirements. Stage 7.
