# Code — the architecture standard a long run can survive on

Read this at stage 3 **before the first line of game code** — the skeleton is
built to this shape, not refactored into it later. Come back whenever `next.py`
prints `ARCH CHECK DUE`, and run the audit below on any existing game handed in
at stage 0.

The standard exists for one reason: a forty-round run compounds whatever
structure round 1 chose. Good structure makes every later round cheaper — a FILL
round drops in a data file, a balance gate greps a JSON, a polish round touches
one module. Bad structure makes every round dearer until the run spends its
firings fighting the code instead of the bar. **Architecture is not a taste
issue here; it is the run's burn rate.**

---

## The layout

```
src/
  core/     loop, time, seeded RNG, save/load, input mapping — engine-agnostic
  systems/  game logic: one file per system from DESIGN.md, no rendering in them
  render/   everything that draws; reads state, never writes it
  ui/       menus and HUD; reads state, emits intents, owns no game state
  data/     every tuning number: balance, waves, tracks, economy — JSON/TS-const
  content/  the stage-5 volume: one file or folder per content unit
```

The names can vary with the stack; the separations cannot. Two of them do most
of the work:

- **simulation / rendering** — systems compute, render draws. This is also what
  makes the harness honest: a headless session runs the simulation without the
  renderer, and a replay is just inputs fed to the simulation.
- **state / ui** — the UI reads state and emits intents ("start race", "buy
  upgrade"); it never mutates game state directly. A UI that owns state is why
  round 30's menu work breaks round 6's save system.

## The rules

Each earns its place by protecting a specific later round.

1. **One seeded RNG, no `Math.random()` in gameplay.** Route every gameplay
   roll through a single generator seeded from the session (URL param, CLI
   flag). This is what makes the filmstrip comparable between rounds — without
   it, round-to-round differences are the dice, not the work. Retrofit is
   miserable; day one is one file.
2. **Fixed timestep, or clamped delta.** Simulation ticks at a fixed rate (or
   dt is clamped and accumulated); rendering interpolates. Unclamped dt means
   physics that differs by frame rate — the capture machine and the player's
   machine play different games, and the soak's fps dip changes the difficulty.
3. **Every tuning number lives in `data/`.** Speeds, costs, HP, spawn tables,
   curve constants — none of them inline in a system. This is the rule that
   pays the most rent: FILL rounds become "add a JSON", balance checks become
   free gates (`references/design.md §6` — arithmetic over data files), and a
   holism fix is a diff of numbers, not a hunt through logic.
4. **Content is data, systems are code.** A track/level/enemy is a data file
   consumed by a loader, never a copy-pasted scene with logic inside. Eight
   tracks as data cost eight files; eight tracks as code cost eight forks that
   drift. This is also what lets a polish round improve *the loader* and have
   all eight units improve at once.
5. **Saves carry a schema version** and one migration function per bump. The
   alternative is discovered in stage 7 as "the soak broke after the update",
   which is the most expensive place to discover anything.
6. **No allocation in the frame loop** (hot paths): pool projectiles, particles
   and vectors; reuse arrays. GC pauses are the fps_min spikes the perf gate
   sees and the player feels; pooling is dull to retrofit and trivial to start.
7. **Systems talk through events or the state, not by calling each other.**
   `combat` emitting `enemy_died` that `economy`, `audio` and `ui` subscribe to
   is also, for free, the metrics hook: the harness's `events` array is just a
   tap on this bus. Direct cross-system calls are why "lighting work broke the
   fail state".
8. **No god object.** A `Game` class over ~200 lines that knows every system by
   name is the tell. It should construct systems and run the loop — nothing
   else.

## The grep gates

Mechanical checks; init.py seeds them into stage 4's gates so they run free
every round. Adapt paths to the project, keep the intent:

```bash
! grep -rn 'Math\.random()' src/systems/ src/content/     # rule 1
grep -rln 'SCHEMA_VERSION' src/core/ | head -1            # rule 5
! grep -rn 'new .*Vector\|\[\]' src/systems/*loop* 2>/dev/null | grep -i 'tick\|update\|frame'  # rule 6, tune per project
test "$(grep -c 'import.*render' src/systems/*.* 2>/dev/null | grep -v ':0' | wc -l)" -eq 0  # sim never imports render
```

Numbers-in-data has no clean grep — it is the first question of the audit below.

---

## The audit — adopted games, and ARCH CHECK DUE

Twenty minutes, and the output is backlog lines, not an essay.

1. Map the actual layout against the one above: where do simulation, rendering,
   state, ui and data actually live? Mixed files are findings.
2. Run the grep gates. Count `Math.random()` call sites, inline tuning numbers
   in systems, cross-system imports.
3. Find the god object: the largest file, and what fraction of systems it
   names.
4. Check the seams the run depends on: can a session run headless? can inputs
   be scripted? does a save survive a version bump?
5. Write the verdict in `DECISIONS.md` — one of **sound** (build on it), **fix
   the seams** (targeted refactors first), **restructure** (the layout itself is
   the finding) — with the three worst findings named.

Every finding becomes one line in `BACKLOG.md`:

    - [ ] stage: <current> — facet: play — refactor: <one seam, one round's worth>

**`refactor:` lines are handed out before feature lines — next.py enforces
this.** On an adopted game with a *restructure* verdict, that means the first
firings build no features at all, and that is correct: every feature built on a
bad seam is built twice.

Two disciplines keep refactoring from becoming its own failure mode:

- **Refactor in rounds, gates green throughout.** Each `refactor:` unit is one
  seam moved with the game still running at the end — a BUILD round like any
  other, judged by gates. "Rewrite it properly" as a single unit is how a run
  loses a week; there is always a one-seam-at-a-time path.
- **A refactor round adds the check that keeps the seam clean** — the grep gate
  or test that would have failed before the refactor. Otherwise round 30
  quietly reintroduces what round 9 removed.
