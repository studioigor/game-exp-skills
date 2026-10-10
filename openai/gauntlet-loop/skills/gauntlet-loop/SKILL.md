---
name: gauntlet-loop
description: "Sequential Gauntlet Loop для Codex: итеративно доводит продукт или артефакт до inspectable эталона раундами «собрал → слепо сравнил → закрыл один главный разрыв», без fan-out субагентов. Подходит для игр, приложений, сайтов, ТЗ, скриншотов, UI, рендеров, 3D, game feel, видео, текста и кода. Для целого продукта сначала требует рабочий вертикальный срез по DELIVERABLE.md; затем использует ротацию линз, commit-then-reveal A/B, состояние на диске и опциональный persistent task/goal layer при его наличии. Использовать, когда явно просят «gauntlet loop», «доведи до уровня X», «улучшай до победы над референсом», «не останавливайся на нормально», «запусти через goal / на ночь», «вот скриншоты — доведи до ума» или другой многократный цикл против образца качества. Не применять для одноразовой правки, обычного аудита или реализации без планки и цикла."
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

# Gauntlet Loop — Codex Goal edition

A method for getting work past "pretty good": give the run a concrete standard it
probably cannot reach, then loop — build, compare against the standard, close the
single biggest gap, repeat — until our output wins or the user stops it.

This sequential version deliberately avoids fan-out. Quality comes from an
inspectable bar, judgement that cannot be rationalised after the fact, and no
permission to stop at good enough:

| Original | Sequential substitute | Why it holds up |
|---|---|---|
| N parallel critics per piece | one critic per round, **rotating lens** | each lens judges a version already hardened by the previous lens, instead of five critics judging the same version |
| fresh agent context per critic | **disk is the context boundary** — the run is resumable from `STATE.md`; Goal continuations and harness compaction may discard chat context safely | a compacted continuation is fresher than a subagent inheriting a briefing |
| builder cannot grade itself | **commit-then-reveal blind A/B** — the verdict is written to disk before the answer key is readable, enforced by `reveal.py` | a verdict that predates the answer cannot be bent to fit it |
| breadth of coverage | **depth of rounds** — one gap per round, many rounds | slower in wall-clock, but each round is small enough to be nearly free |

## Invocation and Codex Goal ownership

- `$gauntlet-loop <objective>` or an explicit natural-language request to run the
  gauntlet starts a run. The input may be abstract, a folder of screenshots, a spec,
  a repo, or one sentence; Phase 1 determines its shape.
- `continue gauntlet <slug>` resumes the disk run. Resolve the slug from
  `.gauntlet/*/STATE.md` when the user omits it and only one run exists.
- An explicit request for a persistent run — `$gauntlet-loop`, `через goal`, `до
  победы`, `не останавливайся`, `на ночь` — authorizes a Codex Goal. Do not infer a
  Goal from an ordinary improvement request merely because this skill triggered.

Before creating a Goal, call `get_goal({})`:

1. Reuse the active Goal when it already owns this gauntlet run.
2. If a different unfinished Goal exists, do not replace it silently; report the
   conflict and continue only within the current turn unless the user resolves it.
3. Otherwise call `create_goal({objective: "..."})`. Make the objective concrete:
   name the deliverable, the inspectable bar, the run slug, and the honest stop
   condition. Pass `token_budget` only when the user explicitly requested a token
   budget. The script's `--budget` is a round count and is not a Goal token budget.

On every Goal continuation call `get_goal({})`, then read `STATE.md`. Use the active
Goal as lifecycle ownership and disk files as detailed round memory. Run a small
batch (normally 2–3 rounds), persist all artifacts, and yield; the Goal harness can
continue in a fresh turn without reconstructing history from chat.

Call `update_goal({status: "complete"})` only after the objective is achieved and no
required work remains. Report the final token usage returned by the tool. Never mark
complete merely because a round or token budget is nearly exhausted. Call
`update_goal({status: "blocked"})` only after the same external blocker has recurred
for three consecutive Goal turns and no meaningful in-scope work remains; ordinary
hard gaps stay in `open_gaps.md` while the loop moves to another gap.

## Run layout

Everything lives on disk, in the project root, so the run survives harness compaction:

```
.gauntlet/<slug>/
  BAR.md          GOAL / BAR / REFERENCE lines — frozen after Phase 2
  RUBRIC.md       the lenses and what each one scores — frozen before round 1
  PIECES.md       the decomposition, one capture command per piece
  DELIVERABLE.md  product runs only — the definition of done, gating every round
  STATE.md        detailed ledger — READ after get_goal on every continuation
  open_gaps.md    the queue of everything noticed but not yet this round's target
  ref/            reference assets (the bar)
  rounds/NN/      artifact.<ext> · ab/{A,B,key.json} · verdict.md · outcome.json
  progress.html   regenerated every round by progress.py
```

`init.py` creates all of it in the exact shapes the other scripts parse. Hand-writing
these files is where runs break: a `RUBRIC.md` whose lenses are prose rather than
`- **name** — question` bullets leaves `next.py` unable to rotate, and that surfaces
at 3am rather than now.

If the project is a git repo, `init.py` adds `.gauntlet/` to `.gitignore` — undo that
if the user wants the run history committed.

## Phase 0 — Resume before anything else

Call `get_goal({})` first when this is a Goal continuation. Then, if
`.gauntlet/*/STATE.md` exists, read it and continue from the last ledger row.
Re-deriving a bar that was already agreed is the most expensive mistake available
here, and it also quietly resets the standard mid-run.

One thing is worth re-judging on resume, though, because it is the only setup error
later rounds cannot fix: `next.py` prints `deliverable:` and `run shape:` together at
the top of every round. Read them as a pair. If the deliverable describes a whole
thing someone uses and the kind names one facet of it, stop — the run is polishing a
corner of something that will never become what was asked for, and forty more rounds
make that worse rather than better. Reinitialise with the right kind.

## Phase 1 — Read what you were handed

The loop is the same whatever the work is. What changes is only three things: which
thing gets judged, what it loses to, and what command produces it. Getting that
mapping wrong is the one setup error the loop cannot recover from — a run that
mistakes the bar for the artifact will spend the night improving the reference.

So answer four questions before touching anything, and the first one is new because
getting it wrong is the most expensive mistake in the whole method:

0. **What does the user get at the end?** — the deliverable. Write it as one sentence
   describing what they are holding when the run finishes, and pass it as
   `--deliverable`; it goes into `BAR.md` and `next.py` reprints it every round.
   Then read that sentence back and pick `--kind` from it. If it describes something
   **someone uses** — a game, an app, a site, a tool — the run is `--kind game` /
   `--kind product`; read `references/product.md` before Phase 2. If it describes **one
   facet** — an image, a spec, a model, a clip — the deliverable and the artifact are
   the same thing and the ordinary loop applies.

   Judge this from the request and its context, not from the words in it. "Сделай
   красиво по этим скринам" about a repo full of game code is a product run; "нужен
   ключевой арт для моей игры" is an image run despite saying game. No script can
   read that difference, and none tries to — `--kind` has no default, `next.py`
   prints the deliverable next to it every round, and the check is yours each time
   you see them together. It is the one decision later rounds cannot repair.
1. **What gets judged each round?** — the artifact. For a product this is several
   things, one per piece, and only one of them is a picture.
2. **What does it lose to?** — the bar. It has to be openable; see `references/bars.md`.
3. **What command produces the artifact?** — the capture. If this run will be
   unattended, that command has to run without a human.

| What you were handed | Artifact each round | Where the bar comes from | Capture |
|---|---|---|---|
| **"make a AAA game" + screenshots** | **per piece: a playtest filmstrip + metrics, a menu flow, a frame** | **outside, per facet: gameplay video, counts, latency targets — screenshots cover only the visual facet** | **a scripted headless session, plus the screenshot script** |
| a project + "make it better" | the built thing, captured | outside: the product, artist or benchmark being chased | the existing build/render/screenshot command |
| screenshots + "make it like this" | our version of the same screen | those screenshots | screenshot script at the reference's viewport |
| screenshots + "here's mine, fix it" | our screen, re-captured every round | **outside** — the screenshots are the starting state, not the standard | a screenshot script you build now |
| a spec (ТЗ) + "build it" | the implementation, section by section | outside: a real product doing the same job | per domain — see `references/bars.md` |
| "write a spec for X" | the spec document itself | a spec of the same class you would be happy to hand a contractor | the document, plus `ab.py --squint` for its outline |
| a repo or module + "improve it" | benchmark output, or the module | a number, or a codebase you would be happy to have authored | the benchmark or test command |
| a render, model, or clip | the rendered frame or clip | the reference image or footage | the frozen render command |
| one sentence ("make it amazing") | pick the smallest thing that can be captured | the strongest inspectable bar available | usually has to be built before round 1 |

**When the input reads two ways, resolve it now.** The classic is a folder of
screenshots: they are the bar if the user is pointing at someone else's work, and
the starting state if they are pointing at their own. Ask once, in one question,
and write the answer into `BAR.md`. Unattended, take the reading that puts the bar
*outside* our own work — a run whose standard is its own starting state can only
ever tie with itself.

Then create the run:

```bash
python3 ~/.codex/skills/gauntlet-loop/scripts/init.py .gauntlet/<slug> \
  --deliverable "<what the user is holding when this finishes>" \
  --goal "<what we are making>" --kind ui --ref path/to/reference.png --budget 40
```

`--kind` is one of `game · product · image · ui · model3d · gamefeel · video · text ·
spec · code` and seeds a starter lens set and free gates for that domain. They are
drafts: adapt them to the bar actually chosen in Phase 3, or the rubric grades a
generic idea of quality rather than the distance to this specific standard.

`game` and `product` also write `DELIVERABLE.md` and switch `next.py` into product
mode, where it will not open a quality round until that file's gates all tick. Pick
them whenever the deliverable is the whole thing rather than one facet of it — a run
started as `--kind image` on a goal that says "game" will do beautiful, useless work.

## Phase 2 — Set the bar

This is the only phase that may need the user, so do it in one pass and then get out
of their way. They came here to hand over a goal and get results, not to configure.

Derive the strongest bar that can actually be opened and compared against. Read
`references/bars.md` for how to pick one per domain and where to get it. Then:

- If the user supplied a reference, or one obvious candidate exists — **take it,
  state it in one sentence, and move on.** Do not ask.
- Ask only when two genuinely different bars would send the work in different
  directions (e.g. photorealism vs stylised). In Plan mode, use
  `request_user_input` when available; otherwise ask one concise question in chat.
  Put the recommended option first.
- **Never ask when the run is unattended** — the prompt says so, it was launched under
  an active Goal for unattended work, or a `## Night run` block already exists. Take the strongest inspectable bar,
  write it into `BAR.md` with the one-sentence justification, note the alternative you
  rejected, and continue. A question asked at launch time blocks until morning, which
  costs more than a bar chosen imperfectly.

`BAR.md` keeps exactly these four lines plus the justification — the scripts parse them:

```
DELIVERABLE: <what the user holds at the end — the thing they will use>
GOAL: <what we are making>
BAR: <the standard, in one sentence, and why it is the right one>
REFERENCE: ref/<file>            # path relative to the run dir
```

The bar does not need to be reachable. Its job is to make "pretty good" visibly
insufficient. If the bar looks reachable in two rounds, raise it.

## Phase 3 — Freeze the rubric and the lens rotation

Before building anything, derive **4–6 lenses** from the bar and write them to
`RUBRIC.md` as `- **name** — the question it asks, and what to look at`.

This happens before round 1 for a specific reason: a rubric written after seeing
the output is a rubric shaped by the output. Once frozen, `RUBRIC.md` may only be
made **stricter**, never looser, and any edit gets a line in `STATE.md` saying what
changed and why. Softening it is how a run ends up declaring victory over a bar it
never met.

Lenses that work almost everywhere:

- **Silhouette / squint** — at 128px, does it read as the same thing at all?
- **Fidelity** — element by element against the bar: what is missing, what is wrong-shaped.
- **Density** — does ours carry as much information, or is it emptier?
- **Craft** — material and light, or rhythm and pacing, or precision, depending on medium.
- **Cohesion** — one authored thing, or assembled parts?
- **First second** — what the bar wins on before any analysis happens.

## Phase 4 — Build the capture harness

Turn the work into something a critic can look at: a render command, a screenshot
script, a recorded clip, a benchmark that prints a number. Build it **once**, freeze
it, and reuse it every round.

This is the highest-leverage step in the whole method. Without a capture, the critic
ends up grading a description of the work, and descriptions always pass. And if the
capture changes between rounds — a moved camera, a different viewport — improvement
becomes indistinguishable from reframing.

Match the capture framing to the reference: same aspect, same angle, same crop.
`ab.py` warns when aspect ratios diverge, because that both leaks which side is
which and means the comparison is measuring the wrong difference.

If the artifact can only be produced by hand — the user has to run the app and
screenshot it themselves — say so plainly and offer the honest alternative: they drop
a file in each round and the loop runs at their pace. That run cannot go overnight,
and pretending otherwise wastes a night.

## Phase 5 — Decompose

Split the goal into the smallest pieces that can be improved and judged
independently, and write them to `PIECES.md` as
`- **name** — capture: <command writing {artifact}>`, noting which part of the bar
each answers to. Keep capture logic frozen but make its destination round-aware:
`{artifact}`, `{round_dir}`, and `{round}` resolve in `next.py`.

Decide the decomposition yourself — the user gave a destination, not a route. By
default a piece keeps the floor until its whole lens rotation has run on it, then
the next piece takes over (`next.py --rotate piece` alternates every round instead,
which suits pieces that interact and can drift apart). Either way, no piece starves:
a run that polishes the first piece for thirty rounds has optimised the wrong thing.

**A piece is a promise of rounds.** Rounds are spent per piece, so anything that is
not a piece gets none, however the goal was worded. This is where a "make it AAA" run
silently becomes a screenshot run: six pieces that are all regions of one frame is six
visual rounds per rotation and nothing ever spent on the thing being used. In product
runs, tag each piece `facet: play|meta|content|ux|audio|visual|perf`; `next.py` enforces
a floor (at least one `play`, surface pieces at most half) and reports it when recent
rounds drift back to the surface anyway.

## Phase 5b — Gate zero: the vertical slice (product runs only)

Before round 1, the product exists end to end. Every gate in `DELIVERABLE.md` ticks:
it starts from one command, a full session runs start to finish, it can be lost or
gotten wrong, it says what happened, nothing dead-ends. Ugly is fine. Incomplete is not.

This ordering is not a preference. A gauntlet is a polishing loop — it makes an
existing thing better one gap at a time — so polish applied to a 40%-built product
produces a beautifully polished 40%, and the missing 60% never surfaces as a gap
because no round is ever pointed at it. The critic only ever sees what the capture
captured.

`next.py` refuses to print a round while any gate is unchecked. When it refuses, the
work is to build the missing part of the product. Trimming the gate list to unblock
the loop is the same move as softening the rubric.

## Phase 6 — The round

This is the loop. Each round targets **one piece** under **one lens** and closes
**one gap**.

**a. Ask what this round is.** One command, instead of re-deriving it from four files:

```bash
python3 ~/.codex/skills/gauntlet-loop/scripts/next.py .gauntlet/<slug>
```

It prints the round number, the lens (the one unused longest, so a skipped or redone
round repairs the rotation instead of corrupting it), the piece, the capture command,
a ready-to-paste `ab.py` invocation, the budget standing, whether a stop condition has
been met, and whether the last few rounds have been chasing the same gap without
moving it. If it reports `SETUP INCOMPLETE`, finish setup rather than improvising —
it means something is still a template placeholder.

**b. Free gates.** Build, typecheck, lint, tests, and the capture itself must
succeed; check any numeric bar. Broken output gets fixed without spending a critic —
there is no point judging a render that failed to render. Record numeric results in
the verdict; they are free signal every round.

In a product run every `check:` in `DELIVERABLE.md` re-runs here. A ticked gate that
stops passing is a regression, and it outranks whatever this round was going to
polish — untick it, fix it, then carry on. This is what catches round 30's lighting
work quietly breaking the fail state round 6 built.

**c. Capture** into `rounds/NN/artifact.<ext>` using the frozen command.

**d. Blind pair** — run the `ab.py` line `next.py` printed. It normalises format and
size (or, for text, formatting and heading style), shuffles the two sides into `A`
and `B`, and writes the key. Do not read `key.json`, and do not `ls -l` the pair —
file sizes are a tell.

**e. Critic pass.** Read **only** `RUBRIC.md`, `open_gaps.md`, and the two sides
(squint or outline versions first, then full). Deliberately do **not** re-read the
code just written, the diff, or the reasoning behind it. The artifact is the thing
being judged; the code is where rationalisation lives, and "but I did that on
purpose" is exactly the thought a separate critic would never have.

Then:

- Score both sides on the frozen rubric under this round's lens.
- **Default to the bar winning.** Only call ours the winner when you can point at
  the specific thing that makes it win under this lens.
- Name **exactly one** gap — the biggest. Not a list. A list becomes a shotgun
  patch, and then nothing tells you which change actually moved the needle.
  Everything else noticed goes to `open_gaps.md`, which is the queue, not this round.

Write `rounds/NN/verdict.md`, ≤12 lines — it exists to steer the next round, not to
document the run:

```markdown
# Round NN — <piece> — lens: <lens>

WINNER: A
GAP: <the single biggest gap, one sentence, phrased as an observable difference>
WHY: <2–3 lines: what the winner does that the loser does not, in rubric terms>
FIX: <the concrete change to make this round>
```

**f. Reveal** — `python3 ~/.codex/skills/gauntlet-loop/scripts/reveal.py .gauntlet/<slug>/rounds/NN`

It refuses to reveal until the verdict is committed with both a `WINNER:` and a
single `GAP:`, then appends the reveal, writes `outcome.json`, and adds the ledger
row itself.

There is one bias this cannot remove: you built the candidate, so you may *recognise*
it rather than judge it. That is why the rubric carries the weight and the A/B is a
check on it, not the other way round. When the reveal says OURS WINS, re-read the
rubric line you scored — if your stated reason does not survive that re-read, treat
it as BAR WINS and keep going.

**g. Builder pass.** Close that one gap. Nothing else, even if something else is
tempting and nearby — that is what the queue is for.

**h. Log** — `python3 ~/.codex/skills/gauntlet-loop/scripts/progress.py .gauntlet/<slug>`

Then go again. Do not narrate every round in prose; `progress.html` and `STATE.md`
are the detailed report. During long tool work, still send concise commentary at
meaningful boundaries and never leave the user without an update for over a minute.

## Phase 7 — When to stop

`next.py` checks the two mechanical conditions every round: **ours wins the blind A/B
on every lens across one full rotation** (a single win is noise, a clean rotation is
a result), and the round budget running out. The third is yours to judge: **two
consecutive rounds where the honest biggest gap is merely cosmetic.**

Treat the round budget according to the Goal objective. If the user asked for "up
to N rounds, then hand over the best result", spending N rounds can satisfy that
bounded objective. If the objective says "beat the bar", budget exhaustion is only
a checkpoint and must not be turned into `update_goal(status="complete")`.

A product run has one condition that outranks all three: **it cannot stop while a
deliverable gate is unchecked.** Winning every lens on something that is not yet the
product the user asked for is not a win, whatever the rotation says.

Never stop on "pretty good", "close enough", or "the remaining gap is hard". Hard
gaps are the entire point of the method. If a gap is genuinely out of reach — it
needs an asset that does not exist, a tool that cannot run here — log it in
`open_gaps.md` as `BLOCKED: <why>` and move to the next gap rather than ending the
run on it.

If `next.py` reports a STALL — the same gap back three rounds running — the gap is
almost certainly phrased as a feeling rather than an observable difference, or the
fix is not landing. Rewrite it as "the bar has X where ours has Y", or mark it
BLOCKED and move on. Grinding is not persistence.

## Phase 8 — Report

Hand over `progress.html` as a clickable absolute local-file link in the final
response. In chat, keep it to a few lines: rounds run, what the final rotation said,
and — importantly — **what still loses to the bar**, from `open_gaps.md`. A gauntlet
run that reports total victory is usually a run whose bar was too low. If a Codex
Goal owns the run and the objective is truly achieved, call `update_goal` before the
final response and include its returned token usage.

## Input-specific recipes

- For a whole game, app, site, or tool, read `references/product.md` in Phase 1.
  Separate deliverable, per-piece artifacts, and per-facet bars; complete the ugly
  vertical slice before quality rounds.
- For specs and screenshot-driven work, read `references/input-patterns.md` in
  Phase 1. It distinguishes a spec as input from a spec as deliverable, and a
  screenshot as external bar from a screenshot as the user's starting state.

## Running it as an unattended Codex Goal

Phases 1–5 are done **with the user present**, then only Phase 6 rounds are left
looping. A bar chosen at 3am either blocks on a question until morning or gets
guessed wrong and forty rounds go into polishing the wrong thing.

**Preflight — prove one full round works end to end** before launching: gates,
capture, blind pair, reveal, fix. `next.py` should print a real round with no
`SETUP INCOMPLETE`. A Goal launched over an unproven capture harness spends the night
failing the same gate.

The night's rules go into `STATE.md`, not only into the Goal objective, because
`STATE.md` is what every continuation reads after `get_goal` and it survives context
compaction:

```markdown
## Night run — <date>
- Budget: stop after round <N>. This cap is what protects the account limit.
- Rounds per Goal turn: 3, then persist state and yield.
- Never ask questions. If a decision is needed, take the option closest to the bar,
  log it under "Decisions taken without asking", and continue.
- Stall guard: if the same free gate fails 3 Goal turns running and nothing else can
  progress, record `BLOCKED: <why>` here and use `update_goal(status="blocked")`.
```

Create the Goal only after this preflight, with an objective that includes the run
slug and stop condition. The active Goal supplies persistence; it does not broaden
filesystem, network, approval, or external-system authority beyond the user's
request.

Each continuation is the same short script: call `get_goal`, read `STATE.md`, run
`next.py`; if it reports incomplete setup, finish setup or record the real blocker
instead of inventing work. Otherwise run two or three rounds, persist state, and
yield. A fresh Goal turn picks up from disk, which is the cheapest critic available.
If `next.py` reports a clean rotation, verify the non-mechanical stop conditions and
deliverable gates before calling `update_goal(status="complete")`.

Three things that kill unattended runs are an operation needing authority the user
did not grant, an unproven capture command, and no review artifact. Resolve needed
authority before launch where possible; never bypass policy or silently expand
scope. For code, preserve a reviewable diff (and commit or branch first only when
the user's workflow authorizes it). Always regenerate `progress.html`.

## Staying inside the limits

The constraint that shapes this whole design. Each rule earns its place:

- **One critic per round, never a fleet.** A round is small; an agent is not.
- **One gap per round.** Keeps rounds small and makes attribution possible.
- **Free gates before paid critique.** Never spend a critic on broken output.
- **The critic's read-set is fixed and small** — rubric, open gaps, two artifacts.
  Never the round history: `STATE.md` and `progress.html` exist for the human.
- **Shrink before viewing.** `ab.py --shrink 1000` by default; a 4K screenshot costs
  several times as much to look at and adds nothing at any of these lenses.
- **Scripts do all the bookkeeping.** Never hand-write the ledger, the progress page,
  or the next round's parameters — that is pure token spend on work a script does
  deterministically, and does not get wrong on round 34.
- **Yield between small batches on long runs.** Goal continuations reload from
  `STATE.md`, so harness compaction at a lens boundary is safe and gives the critic
  a smaller read-set.

**Optional cold critic.** Only if the user explicitly requests subagents,
delegation, or parallel agent work, spawning **one**
at a lens boundary (say every fourth round) restores true blindness where it matters
most: read `RUBRIC.md`, look at `ab/A` and `ab/B`, return `WINNER` plus one gap,
nothing else. One agent every four rounds costs a small fraction of a single
fan-out round. This is worth most on text runs, where self-recognition is strongest.
Never spawn more than one at a time, and never one per lens — that is the fan-out
this skill exists to avoid. Default is off; permission to run the Gauntlet itself
is not permission to spawn a subagent.

## Failure modes

| Symptom | What is actually wrong | Fix |
|---|---|---|
| A gorgeous screenshot and no game | the goal was a product, the run was set up around an image bar | `--kind game`, `DELIVERABLE.md`, vertical slice first — `references/product.md` |
| Every piece is a region of one frame | the decomposition came from the artifact instead of the product | facet-tag the pieces; `next.py` blocks a surface-only set |
| Late rounds all land on the frame again | the visual piece is the easiest to capture, so it wins by default | `next.py` reports SURFACE DRIFT — take the starving piece next |
| Rounds stop changing anything | the gap is phrased as a feeling, not an observable difference | rewrite it as "the bar has X where ours has Y" — `next.py` flags this as STALL |
| Every round says OURS WINS | self-recognition plus a soft rubric | tighten the rubric, raise the bar, consider one cold critic |
| The rubric got easier over the run | goalpost drift | rubric is stricter-only; log every edit in `STATE.md` |
| Fixed five things, output got worse | shotgun patching | one gap per round, the rest to the queue |
| Cannot tell if anything improved | no frozen capture, or the capture changed | freeze the capture command in Phase 4 |
| The bar is "make it look professional" | not inspectable | get a file, a URL, or a number — see `references/bars.md` |
| The bar is our own starting screenshot | the run can only tie with itself | the bar comes from outside our work, always |
| Thirty rounds on the same piece | no rotation across pieces | `next.py` moves on after a full lens rotation; check `PIECES.md` has more than one |
| Overnight run did nothing all night | a permission prompt, or setup was never finished | preflight one full round; pre-approve the commands |

## Bundled files

- `scripts/init.py` — creates the run skeleton in the shapes the other scripts parse.
- `scripts/next.py` — what the next round is: lens, piece, capture, budget, stop check.
- `scripts/ab.py` — blind pair setup: normalises, shuffles, writes the key.
- `scripts/reveal.py` — enforces commit-then-reveal, writes the ledger row.
- `scripts/progress.py` — regenerates the self-contained live progress page.
- `references/bars.md` — how to choose a bar and build a capture harness, per domain.
- `references/product.md` — read first when the deliverable is a whole product:
  deliverable vs artifact, the vertical slice, facet decomposition, per-facet bars,
  and the playtest capture that makes a loop inspectable.
