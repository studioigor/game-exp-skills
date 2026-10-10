# Bars — one per facet, and where each comes from

Read this at stage 2, when filling `BARS.md`.

**A game has no single bar.** This is the most important sentence in the file. The
screenshots the user handed over say what a game *looks like* and nothing at all
about what it *plays like*, and what it plays like is most of what "clone of NFS"
or "AAA game" ever meant.

So: eight facets, eight standards. `visual` is one of them.

---

## What makes a bar a bar

Three questions. A bar that fails any of them turns the loop into
self-congratulation, because a critic that cannot look at the standard scores
intent instead of output.

1. **Can it be opened?** A file, a URL, a recording, a number produced by a
   command. "Make it look professional" is not a bar.
2. **Is it out of reach?** If it can plausibly be matched in two rounds it will not
   stop the run settling. The bar being unreachable is the feature.
3. **Does it compare like with like?** Same framing, same aspect, same scenario,
   same subject. A 1440px marketing shot against a 390px mobile view measures the
   framing, not the work.

Numbers make the strongest bars, because free gates can check them every round
without spending a critic. Reach for a number wherever one exists.

---

## The eight facets

### `play` — the loop itself

- **Bar** — 30–60 seconds of the reference title doing the same activity, cut into
  a filmstrip at the same interval as ours. Plus the numbers pulled out of it:
  time to first meaningful action, actions per minute, how long one run lasts,
  how often the state changes, how many distinct things happen per 30 seconds.
- **Capture** — the scripted session's filmstrip.
- **Reading it** — read *across* the strip, not at any single frame. What is
  happening per frame on the bar that is not happening on ours? Where does the
  bar's state change and ours stay still? At the moment of the key action, how
  many frames show a response? Could a stranger tell from the strip alone what the
  player was trying to do and whether they succeeded?
- **Where to get it** — a gameplay video. If nothing can be recorded here, the
  user watching 60 seconds and answering five specific questions is a perfectly
  good bar and costs them a minute.

### `feel` — control

- **Bar** — **a number**, and this is the facet where that is easiest: input to
  visible response in milliseconds, frames from press to first movement, frames
  for the response to settle. Reference titles in most genres land at 2–4 frames
  to first visible change.
- **Capture** — an instrumented input trace, or frame samples around a scripted
  input.
- **Free gate** — because it is a number, this facet mostly does not need critic
  rounds at all. Assert the threshold and let it run every round.

### `meta` — what carries between sessions

- **Bar** — an inventory of the reference: how many upgrades, how many tiers, how
  long to see it all, what persists, what resets.
- **Capture** — the save file, the progression screen, the metrics JSON across
  several scripted sessions.

### `content` — how much there is

- **Bar** — `CONTRACT.md`. This facet's bar is already written and already
  counted; `contract.py` is its critic.
- **Watch for** — the count met by N copies of one thing. Variety is the actual
  bar; if two units cannot be told apart in the filmstrip, they are one unit.

### `ux` — the flow

- **Bar** — the reference's flow captured screen by screen: how many taps from
  launch to playing, what it explains and when, what it never explains at all.
- **Capture** — the screenshot script at each screen, plus the **first session**
  capture from a cold start.
- **The one that matters most** — the first sixty seconds. Everything looks
  learnable to the person who built it, which is exactly why this needs a capture
  rather than an opinion.

### `audio` — the half of feel that is not visible

- **Bar** — a reference clip, plus counts: how many *distinct* SFX fire in 30
  seconds of the bar versus ours; is there music; does it react to state.
- **Capture** — the session's audio track, or an event log of every sound
  triggered.
- **Cheap and brutal** — "which actions answer in sound on the bar and are silent
  on ours" is a list you can write in five minutes, and it is usually long.

### `perf` — does it hold

- **Bar** — a number: target frame rate at target scene complexity on the target
  device. Not the average — the **worst moment**, which is what a player feels.
- **Capture** — the perf command, plus `fps_min` from every session's metrics.

### `visual` — the frame

- **Bar** — two things at once, and the second is the one runs forget: the
  reference screenshots (matched framing, matched viewport, matched moment) say
  what *kind* of thing this looks like — and **the ceiling of the stack plus
  `ART.md`** says how good it is allowed to look. Parity with the reference is
  not the bar; a run that reaches "roughly like the screenshot" with default
  lighting and no post chain has matched the subject and missed the craft.
- **Capture** — the screenshot script.
- **Lenses** — silhouette at 128px, value structure with the hue ignored, material
  and light, cohesion — plus the two ceiling lenses from `references/art.md`:
  **signature** (are ART.md's named techniques on screen? would this frame be
  recognised among a hundred genre-mates?) and **density** (how many layers of
  visual work are in frame — authored light, post chain, particles, background
  motion, camera life).
- **Not won until** — the post-processing chain is live and tuned and the ART.md
  signature techniques are visible in the capture. A clean-but-plain frame can
  win the first four lenses and still be nowhere near the ceiling; the two extra
  lenses exist so that loss is visible.
- **Remember what this is** — one facet of eight. It is the easiest to capture and
  the most satisfying to improve, which is exactly why a run drifts here and stays.

---

## Typical numbers, by genre

Starting values for BARS.md when the reference cannot be measured today. Every
one is replaceable by a measured number from the actual reference — these exist
so stage 2 closes in minutes, not so it skips the measuring forever. Web/casual
context; premium PC skews longer everywhere.

| | time to first action | one meso-cycle | fail/retry rhythm | distinct SFX per 30s | fps floor (mobile web) |
|---|---|---|---|---|---|
| **arcade racer** | < 20s | 60–180s race | retry < 3s after fail | 10–15 (engine, drift, traffic, pickups, UI) | 30, target 60 |
| **platformer** | < 15s | 45–120s level | death→respawn < 2s | 8–12 | 60 |
| **survival / crafting** | < 45s | 5–10 min day-cycle or goal | soft fail, pressure waves | 10–14 (ambient counts) | 30 |
| **roguelike / arena** | < 20s | 3–8 min run | run end→new run < 5s | 12–18 | 30, target 60 |
| **tower defense** | < 30s | 2–5 min wave-set | lose wave, replay wave | 8–12 | 30 |
| **idle / management** | < 10s | 30–90s decision beat | no fail; stall = fail | 6–10 | 30 |

Cross-genre constants worth asserting as free gates: input→response under 100ms
(2–4 frames to first visible change); load to playable under 5s cold on web;
one session's natural stop between 5 and 20 minutes for casual platforms.

## Reading numbers off a reference video — the ten-minute protocol

One gameplay video of the reference title, watched twice with a notepad. This is
where the `play`, `feel` and `audio` bars get their numbers, and it costs ten
minutes once:

1. **First watch, feel the shape**: when did the first meaningful action happen
   (timestamp)? When did the first failure or near-miss happen? Where did you
   feel the intensity peak?
2. **Second watch, count 30 representative seconds**: distinct player verbs ·
   state changes (score, damage, pickups, phase) · distinct sounds · camera
   events (shake, zoom, cut). Write four numbers.
3. **Frame-step the key action** (`,`/`.` in YouTube): frames from input-moment
   to first visible response, and how many simultaneous answers fire (motion +
   flash + particles + sound).
4. Transfer straight into BARS.md lines: the four counts become `play` and
   `audio` bars; the frame counts become the `feel` bar; your two timestamps
   become `ux` (time to first action) and pacing (`play`).

## The juice checklist — `feel`'s countable half

Score ours and the bar side by side; each line is present/absent, so the gap is
a number, not a feeling. The bar for a polished action game is most of this
list firing on the *primary* action:

- [ ] hit-stop (2–6 frames of freeze on significant impact)
- [ ] screen shake with rotation, scaled to impact, never constant
- [ ] flash — target flash on hit, 1-frame full-screen tint ≤10% on big events
- [ ] particles on: impact, movement (dust/trail), destruction, pickup
- [ ] squash & stretch or scale-punch on the acting object
- [ ] easing curves on every moving UI/camera element (nothing linear)
- [ ] sound layered with the above in the same 2–3 frames
- [ ] controller/haptic or visual recoil on the input source itself
- [ ] slow-motion or zoom on the climax moment (used sparingly)
- [ ] idle motion — nothing on screen is perfectly still

Restraint is the eleventh line: the lens `feel/restraint` exists because ten
overlapping effects at full volume is noise. The bar's version of this list is
usually "all present, each quieter than you expect".

---

## Where bars come from, in order of preference

1. **The user handed one over** — a screenshot, a video, a link, "make it like
   that". Use it; do not improve on it.
2. **A real exemplar you can capture** — the actual game being chased. A gameplay
   video is on YouTube; a screenshot is one search away; a browser can capture a
   web game directly. One hour here is worth twenty rounds later.
3. **A measurable ceiling** — 60fps at 4× the object count, sub-60ms input
   latency, 12 distinct SFX per 30 seconds, 8 tracks. Strongest kind, because free
   gates check it without a critic.
4. **Your own best previous work** — a past build, the best level in the project.
   Weaker (it drifts with taste) but real and inspectable.
5. **A generated straw-man ceiling** — build one deliberately over-the-top version,
   freeze it as `ref/`, beat it. Last resort: it can only be as ambitious as the
   first attempt was.

Never let the bar be the run's own starting state. A run whose standard is where it
started can only ever tie with itself.

---

## Screenshots: bar or starting state?

The most common ambiguous input, and the run breaks if the two are confused.
Settle it in stage 0 and write the answer into `BRIEF.md`.

- **As the bar** — someone else's game: "make it like this". Copy into `ref/`,
  match the capture to their framing exactly.
- **As the starting state** — the user's own: "here's mine, fix it". These are
  round zero's artifact, not the standard. The bar must still come from outside or
  the run tops out at *slightly better than the screenshot I was given*. Asking for
  one reference shot costs the user thirty seconds and is what makes the rest of
  the run mean anything.

Unattended, always take the reading that puts the bar **outside** our own work.
