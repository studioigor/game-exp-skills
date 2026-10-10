# Ship — the gates between "works here" and "a stranger can play it"

Read this at stage 7.

Everything before this stage made the game good. This stage makes it *survivable*:
the failures here are the ones that only appear on someone else's machine, on
their second evening, or in the first thirty seconds before they ever reach the
part that was polished.

---

## 1. The soak session

A soak is an extended run — 30 minutes to a few hours — with specific things being
watched. It is not a longer playtest; it hunts a different class of bug entirely,
and none of them appear in a 30-second filmstrip.

Run the SOAK command from `HARNESS.md` at the target session length, recording at
checkpoints (T+0, T+15, T+30, T+45, T+60 for an hour).

| What to watch | What failure looks like | Why it only shows up here |
|---|---|---|
| **Memory** | heap grows and never returns after a scene change | one leak is invisible; forty scene transitions are not |
| **Frame time** | fps_mean drifts down across checkpoints | the first minute is always the fastest minute |
| **State accumulation** | breaks after N repetitions — inventory fills, a counter overflows, AI state corrupts, a list never gets pruned | needs N repetitions by definition |
| **Content exhaustion** | the player has seen everything and the loop keeps asking | the whole point of the contract, verified |
| **Fun fatigue** | the mechanic that felt great in minute two is tiring by minute forty | short sessions systematically flatter a game |

The first three are mechanical: compare metrics across checkpoints and assert. The
last two need a read of the strip, and they are the ones that decide whether an
evening with this game is any good.

A regression soak after any memory or stability fix is worth its cost.

### Performance budgets — assert, don't eyeball

The numbers the soak's metrics get compared against. Adjust per project, then
write them as free gates so they run every round from here on:

| Metric | Web desktop | Web mobile | Why this number |
|---|---|---|---|
| fps floor (worst moment) | 60 | 30 | the worst moment is what a player feels |
| frame-time p95 | < 20ms | < 37ms | catches stutter a mean hides |
| JS heap after 30 min | < 250MB and **flat** | < 150MB and flat | growth = leak, whatever the absolute |
| draw calls per frame | < 200 | < 100 | the instancing check in one number |
| cold load → playable | < 5s | < 8s | past this, players leave before frame one |
| total download | < 50MB | < 25MB | Яндекс/portal audiences are on real networks |

### Save compatibility

Ship-blocking because it destroys exactly the players who liked the game most.
Take a save file from the *oldest surviving build* (keep one per closed stage —
the per-stage commits make this free), load it in the ship candidate, and play
one full cycle. A missing field, a renamed system or a re-based currency shows
up here and nowhere else. If `references/code.md` rule 5 was followed this is
one migration function per schema bump; if it was not, this check is how you
find out before the players do.

---

## 2. The placeholder sweep

Everything the build ships must be intended. Grep for the whole family:

```bash
grep -rniE 'lorem|placeholder|TODO|FIXME|XXX|test123|asdf|debug|dummy|temp' \
  --include='*.js' --include='*.ts' --include='*.html' --include='*.css' \
  --include='*.json' src/ assets/ 2>/dev/null
grep -rn 'console\.\(log\|debug\|warn\)' src/ | grep -v '^\s*//'
```

Also by eye, because grep will not catch these:

- placeholder art still in the build (the grey box, the untextured cube, the
  default cube-man);
- a debug camera, a god mode, a level-skip key still bound;
- default names — "New Game 1", "Player", "Untitled";
- an unstyled browser `alert()` or `confirm()`;
- the developer's own test save shipped as the initial state.

Any one of these is the first thing a player sees, because they are always in the
menu or the first level — the parts built earliest and looked at least.

---

## 3. Feedback completeness

Walk every player action and ask two questions: does it answer in **sound**, and
does it answer in **motion**? A silent action reads as a broken action, and this is
the cheapest remaining improvement in almost every build that reaches this stage.

The list that is usually incomplete: menu navigation and selection, an invalid or
refused action, taking and dealing damage, picking something up, saving, an error,
completing an objective, failing, level start, level end.

Then check the mix: nothing painfully loud, nothing inaudible, nothing fighting
the music.

---

## 4. First-run and cold-start

Run the FIRST SESSION capture and read the strip as a stranger:

- [ ] it starts from one command / one click on a clean machine
- [ ] no saved state, no unlocks, no assumptions from a previous run
- [ ] the player reaches the core activity without being told how
- [ ] time to first meaningful action is inside the target
- [ ] every screen has a way out; nothing dead-ends
- [ ] failure is visible and says what happened
- [ ] state survives a reload
- [ ] every path either works or fails legibly — no silent nothing

---

## 5. Platform requirements

### A web game portal (Яндекс Игры, Poki, CrazyGames, itch)

Two separate jobs, and both are the platform's own documentation rather than
something to guess at: the **SDK integration** (init, ads, player auth, saves,
leaderboards, purchases, gameplay events, compliance) and the **store card**
(icon, cover, promo screenshots, every text field, usually in more than one
language). Read the portal's current docs when you get there — these APIs and
asset sizes change, and a stale reimplementation costs a review rejection.

The platform gates worth checking before either: the game loads inside an iframe,
it handles pause/resume when an ad plays, it works on touch as well as keyboard, it
survives a device rotation, and nothing blocks on a network call that may not
return.

### itch.io / self-hosted web

The zero-gatekeeper path — worth shipping to even when Яндекс is the real
target, because it is a same-day release valve and a playtest channel:

- one folder, `index.html` at its root, **all paths relative** (`./`), zipped;
- no SDK calls left in this build (guard the Яндекс SDK behind an environment
  check rather than maintaining two builds);
- set the embed viewport to the game's design resolution; enable fullscreen;
- itch uploads are immutable per file — version the zip name (`game-1.0.3.zip`).

### Web generally

- [ ] works at the smallest supported width without horizontal scroll
- [ ] no external requests that can fail silently
- [ ] first meaningful frame inside the load-time target on a cold cache
- [ ] touch input works, not just mouse
- [ ] audio starts only after a user gesture (browsers block it otherwise, and
      this failure is silent and total)

---

## 6. The final report

When the ladder closes, the report to the user is short and it leads with what did
*not* get done:

1. **every gate and contract line that shipped `BLOCKED`**, with its reason —
   first, plainly, before any good news;
2. what still loses to the bar, per facet, from `open_gaps.md`;
3. rounds run, and what the last rotation said;
4. `progress.html` (`SendUserFile`, or publish it as an Artifact for a link).

A run that reports total victory is usually a run whose bar was too low. If nothing
in `open_gaps.md` is still losing to the reference title, the honest conclusion is
that the reference was not being looked at hard enough — not that the clone beat it.
