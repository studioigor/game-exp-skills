# When the deliverable is a whole product

Read this in Phase 1 whenever the goal names a **thing that gets used** — a game, an
app, a site, a tool — rather than one facet of one. `--kind game` and `--kind product`
are for exactly this, and they behave differently from every other kind in two ways:
they carry `DELIVERABLE.md`, and `next.py` refuses to open a quality round while a
gate in it is unchecked.

## The failure this exists to prevent

"Make an AAA game, here are screenshots" is the single most common way a gauntlet run
delivers the wrong thing. The mechanism is worth spelling out, because every step of
it looks correct from inside:

1. The screenshots are the only inspectable thing on the table, so they become the bar.
2. A screenshot bar can only be compared against a screenshot, so the artifact becomes
   a captured frame.
3. A frame decomposes into regions — city, road, car, HUD, grade — so the pieces
   become regions of a frame.
4. Regions of a frame can only be judged by visual lenses, so the rubric becomes
   silhouette, value, density, material.
5. Forty rounds later there is a stunning frame, a wet street, a beautiful car —
   and no game. Nothing ever drove, nobody could lose, and there was no reason to
   press start twice.

Every step follows from the one before it. The error is at step 1, and it is
unrecoverable later — a run cannot round-trip its way from a screenshot bar to a
playable product, because none of the rounds are ever pointed at the product.

So: **the reference is a facet of the bar, never the whole bar.** Screenshots of
a shipped game say what it looks like. They say nothing about what it plays like,
and "what it plays like" is most of what "AAA game" means.

## Split the goal before anything else

Three separate things, and conflating any two of them is what breaks the run:

| | What it is | Where it lives |
|---|---|---|
| **Deliverable** | the product the user will actually use | `DELIVERABLE.md` — the definition of done |
| **Artifacts** | what a round captures and judges, one per piece | `PIECES.md` — one capture command each |
| **Bar** | the standard each artifact loses to | `BAR.md` + `ref/` — one reference per facet |

A screenshot is an artifact. A game is a deliverable. The whole method operates on
artifacts, which is why the deliverable needs its own file and its own enforcement:
nothing in the loop protects it otherwise.

## Gate zero — the vertical slice comes before round 1

Build the whole product end to end, ugly, before the first quality round. Every gate
in `DELIVERABLE.md` ticks. It boots, it can be played or used start to finish, it can
be lost or gotten wrong, it says what happened, and nothing dead-ends.

This ordering is not a preference. A gauntlet is a polishing loop: it makes an existing
thing better, one gap at a time. Polish applied to a product that is 40% built produces
a beautifully polished 40%, and the missing 60% never shows up as a gap because no
round is ever pointed at it — the critic only ever sees what the capture captured.

`next.py` enforces this by refusing to print a round while a gate is unchecked. When
it refuses, the answer is to build the missing part of the product, not to trim the
gate list.

An ugly complete product is worth more than a gorgeous fragment, and it is also the
only thing the rest of the run can operate on.

## Writing DELIVERABLE.md

8–12 gates. Must-haves only — every extra gate is a quality round that does not happen,
and every missing must-have is a hole the loop cannot see.

```
- [ ] <what must be true of the product> — check: <command, or `manual: <what to do>`>
```

For a game, the gates almost always include: it starts from one command; a first-time
player reaches the core activity without being told how; a full session runs start to
finish; **it is possible to lose**; there is a reason to press restart; every input
answers in sound and motion; there is enough content that a session does not run out;
it holds its frame rate; nothing shipped is placeholder or debug; it runs on the target
device.

For an app or site: the core job completes on a cold start; every path either works or
fails visibly; state survives a reload; errors are legible; it works at the smallest
supported width; nothing is lorem.

A `check:` that is a command is worth several that are prose — it runs free every round
and catches the regression where round 30's visual work quietly breaks the thing round
6 built. `manual:` is allowed, but each one is a gate the loop cannot verify unattended,
so keep them few and write exactly what to do.

A gate that cannot be met in this environment gets `BLOCKED: <why>` in its text. It
stops blocking, it gets reported at the end, and it does not get deleted — a deleted
gate is a lowered standard that leaves no trace.

## Decomposing into pieces

A piece is a promise of rounds. Rounds are spent per piece, so whatever is not a piece
gets no rounds, however the goal was worded. Tag each with a facet:

- `play` — mechanics, the loop, control feel, difficulty
- `meta` — progression, save, economy, unlocks, what carries between sessions
- `content` — how much there is and how varied
- `ux` — flow between screens, onboarding, menus, error paths
- `audio` — music, SFX, mix
- `visual` — the frame: world, materials, light, grade
- `perf` — frame rate, load, memory, stability over a long session

`next.py` enforces a floor: at least one `play` piece, and `visual` + `ux` no more than
half the total. That floor is deliberately weak — it catches the run that is *entirely*
surface, not the run that is merely lopsided. Judge the balance yourself against what
the product is actually short of.

Order matters: pieces are worked in the order listed, so put the facet the product most
fails at first and `visual` last. A run that starts on the frame tends to stay there.

## Bars for the facets a screenshot cannot cover

Each facet needs its own inspectable standard. This is the work that makes a product
run real, and it is worth an hour up front:

- **play** — a gameplay video of the reference title (30–60s of the same activity),
  cut into a filmstrip at fixed intervals. Compared against our own filmstrip from the
  same scenario, it shows pacing, reaction, feedback density and what is happening on
  screen per second. Also: the numbers pulled from that video — time to first action,
  actions per minute, how long a run lasts, how often the state changes.
- **control feel** — measurable and therefore strong: input-to-response latency in ms,
  frames from press to visible change, how many frames the response takes to settle.
  Free gates check these every round without a critic.
- **meta / content** — an inventory of the reference: how many levels, cars, enemies,
  upgrades, hours to see everything. A count is a bar. Ours next to theirs is a gap
  that cannot be argued with.
- **audio** — a reference clip, plus counts: how many distinct SFX fire in 30 seconds
  of the bar versus ours; is there music, does it react.
- **ux** — the reference's flow captured screen by screen: how many taps from launch
  to playing, what it explains and when.
- **perf** — a number: the target frame rate at the target scene complexity, on the
  target device.
- **visual** — the screenshots. One facet of six.

If the reference title cannot be recorded here, the user watching 60 seconds of it and
answering five specific questions is a perfectly good bar, and it costs them a minute.

## The playtest capture

The single highest-leverage thing built in a product run. A static screenshot cannot
show a loop, so build a scripted session that runs headless and emits both:

- **a filmstrip** — frames at a fixed interval across a fixed scenario (same seed, same
  inputs, same duration), tiled into one image. This is what goes into the blind A/B
  against the reference video's filmstrip. A loop is visible in a filmstrip and
  invisible in a frame.
- **a metrics JSON** — did the session complete, how long it took, frame rate min/mean,
  every state change with a timestamp, inputs, score, deaths, events fired. Half the
  product lenses can be scored off numbers, and numbers are free every round.

Determinism matters more here than anywhere: fixed seed, scripted inputs, fixed
duration. Without it, round-to-round differences are the RNG rather than the work.

Freeze it in Phase 4 and reuse it every round, same as any other capture. It is also
what makes the free gates strong enough to run a product overnight — a session that
fails to complete fails the gate before a critic is ever spent.

## Judging a filmstrip

Score the loop, not the frames — the frames have their own lens and their own rounds.
Under a `play` lens, read across the strip:

- What is *happening* per frame on the bar that is not happening on ours?
- Where does the bar's state change and ours stay still?
- At the moment of the key action, how many frames show a response — and how many of
  ours do?
- Could a stranger tell from the strip alone what the player was trying to do, and
  whether they succeeded?

The most common honest verdict on an early product run is "the bar's strip shows six
things happening and ours shows the same picture six times". That is a `play` gap and
it is worth ten visual ones.

## Stopping

The mechanical stop conditions are unchanged (a clean rotation, or the budget), plus
one more that outranks them: **a product run cannot stop while a deliverable gate is
unchecked**, whatever the rotation says. Winning every visual lens on an unfinished
product is not a win.

Report at the end: rounds run, what the last rotation said, what still loses to the
bar per facet, and — first, plainly — every gate that shipped `BLOCKED`.
