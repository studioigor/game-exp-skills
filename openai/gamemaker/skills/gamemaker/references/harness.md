# Harness — building the capture, and proving it

Read this at stage 2. It is the highest-leverage hour in the whole run: without a
capture, the critic grades a *description* of the game, and descriptions always
pass. Everything downstream — every gate, every blind pair, every night — runs on
what gets built here.

---

## The rule that decides the stack

**A stack whose session cannot be recorded without a human cannot be run
overnight.** That is the whole constraint. Everything else about engine choice is
negotiable; this is not, because failing it does not produce a worse run, it
produces a run that stops at 00:05 and nobody finds out until morning.

So when the choice is open, take them in this order:

| Stack | Headless capture | Verdict for a night run |
|---|---|---|
| **Web** — Three.js, canvas, DOM | Playwright / Puppeteer: real browser, no window, screenshots and video, JS evaluated in-page for metrics | **best.** Works today, no licence, no display server, and the shortest path to a web portal release. |
| **Godot 4** | `godot --headless --script` runs a scripted scene and writes frames | **good.** Real, well documented, no licence server. |
| **Unity** | needs a licence check-in and, on macOS, usually a window | **poor.** Say so before the night, not after. |
| **Unreal** | heavy, slow, licence-free but rarely scriptable in one command here | **poor** for this loop. |

If the user has already fixed a stack from the poor rows, do not pretend. Say
plainly that unattended rounds are not available, and offer the honest
alternative: they run the game and drop a recording into `rounds/NN/` each round,
and the loop proceeds at their pace. That run still works — it just cannot go
overnight, and knowing that up front is worth a night.

---

## What the harness must emit

Two artifacts, from one command, every round.

### The filmstrip

Frames at a fixed interval across a fixed scenario, tiled into a single image.

**This is the single most important idea in the whole harness.** A loop is visible
in a filmstrip and completely invisible in a single frame. The most common honest
verdict on an early run is *"the bar's strip shows six things happening and ours
shows the same picture six times"* — that is one `play` gap worth ten visual ones,
and no screenshot could ever have surfaced it.

Determinism matters more here than anywhere else in the run:

- **fixed seed** — same RNG every round;
- **scripted inputs** — the same sequence of moves, not a live player;
- **fixed duration** — the same number of seconds;
- **fixed framing** — same camera, same viewport, same crop.

Without those, round-to-round differences are the RNG rather than the work, and
improvement is indistinguishable from luck.

### The metrics JSON

At minimum:

```json
{
  "completed": true,
  "duration": 182.4,
  "fps_mean": 58.7,
  "fps_min": 41.0,
  "state_changes": 14,
  "events": ["race_start", "police_engaged", "heat_2", "busted"],
  "score": 12400,
  "deaths": 1,
  "time_to_first_action": 3.2
}
```

Half the lenses can be scored off numbers, and numbers are free every round — no
critic, no tokens, no self-recognition problem. Every metric you add here is a lens
you never have to pay for again.

`completed` in particular is what makes a night safe: a session that fails to
finish fails the gate before a critic is ever spent.

---

## The five frozen commands

Write them into `HARNESS.md` and never touch them again.

1. **SESSION** — the scripted run above. The `play` facet's capture.
2. **SCREENSHOT** — fixed viewport, matched to the reference's framing. The
   `visual` and `ux` capture. Match aspect and crop to the reference or the
   comparison measures the framing rather than the work.
3. **FIRST SESSION** — the same scripted run from a **cold start**, no saved
   state, no unlocks. This is what "a first-time player reaches the core activity
   without being told how" is actually read from, and it is the capture most runs
   forget to build. Everything looks learnable to the person who built it.
4. **PERF** — frame rate at target complexity on the target device. A number.
5. **SOAK** — the long session, for stage 7. Same scenario, many minutes.

---

## Proving it

Stage 2 does not close on a claim that the capture works. It closes when the
command has actually run and produced files. Then set `CAPTURE PROVEN: yes` in
`HARNESS.md`; `next.py` warns every round until you do.

A quick sanity list before you flip it:

- [ ] one command, no arguments a human has to think about
- [ ] no window opens
- [ ] runs from a clean shell, not from an editor
- [ ] writes real files to the round directory
- [ ] the metrics JSON parses and has non-null numbers in it
- [ ] running it twice with the same seed produces the same metrics
- [ ] it exits non-zero when the session fails, so it works as a gate

That last one matters more than it looks: a capture that exits 0 after failing
turns every free gate downstream into a no-op.

---

## Web specifics (the default path)

**Start from the bundled template, not from scratch:**
`~/.claude/skills/gamemaker/scripts/templates/capture_web.mjs` is a complete
working capture — serve, fixed viewport, `?seed=&replay=`, scheduled synthetic
inputs, frames, tiling, `window.__metrics`, non-zero exit on failure. Copy it
into the project as `tools/capture.mjs`, adapt the input schedule and the URL,
and stage 2 becomes an hour shorter. The notes below are what the template
implements and why.

Playwright is not installed by default on this machine — check and install it in
stage 2 rather than assuming:

```bash
python3 -c "import shutil,sys; sys.exit(0 if shutil.which('npx') else 1)" \
  && npx --yes playwright install chromium
```

The shape that works:

- serve the build on a local port (`npx serve`, `python3 -m http.server`, vite preview);
- launch chromium headless at a fixed viewport with a fixed device scale;
- expose a hook the page can write to — `window.__metrics` — and have the game push
  events into it;
- drive input by dispatching synthetic key/pointer events on a fixed schedule, or
  better, by putting the game into a `?replay=<script>` mode that reads a canned
  input sequence. A replay mode is more work once and far more reliable forever.
- screenshot on a timer into a frames directory, then tile with `sips` / `ffmpeg` /
  a tiny canvas script;
- read `window.__metrics` at the end and write it out as JSON.

Seed the RNG from a URL parameter and never call `Math.random()` directly anywhere
in gameplay code — route it all through one seeded generator. This is the single
change that makes everything else reproducible, and retrofitting it later is
miserable.

---

## Godot specifics

Bundled starting point: `~/.claude/skills/gamemaker/scripts/templates/session.gd`
— copy into the project as `tools/session.gd` and adapt the input schedule.

```bash
godot --headless --path . --script res://tools/session.gd -- --seed 7 --out <dir>
```

Drive input with `Input.parse_input_event` on a fixed timer, capture frames with
`get_viewport().get_texture().get_image().save_png()`, and write metrics with
`JSON.stringify` to the out directory. Fix the physics tick and use a fixed delta
so the scripted run is deterministic.

---

## Two recipes worth the hour they cost

### Measuring input latency (the `feel` bar's number)

In-page, no camera needed. Record `performance.now()` at the moment the
synthetic input is dispatched, and have the game write `performance.now()` when
the first frame *reflecting that input* renders (set a flag in the input
handler; clear it in the render loop and log the delta). Push each sample into
`window.__metrics.input_latency_ms`. Ten scripted presses → mean and worst. The
same instrument becomes the free gate `feel` runs every round: assert
`p95 < 100ms`. In Godot, the equivalent pair is `Time.get_ticks_usec()` at
`parse_input_event` and in the next `_process` that consumes it.

### The audio event log (the `audio` capture)

Headless browsers do not play sound, so do not capture sound — capture
*intent*. Route every sound trigger through one `playSound(name)` function (the
event-bus tap from `references/code.md` rule 7), and in capture mode have it
append `{t, name}` to `window.__metrics.audio_events` instead of (or as well
as) playing. The session then yields, for free: distinct sounds per 30s
(compare against the bar's count), actions that fired silently (diff the events
array against the input schedule), and music state changes. The `audio` facet
becomes half free-gate, and the critic reads a list instead of listening.

---

## When the capture genuinely cannot be built

Say so, and say it early. Then offer the user-paced mode: they run the game, drop
a recording or a screenshot into `rounds/NN/`, and the loop does everything else.
That run is real and it works — it just runs at their pace and it cannot go
overnight. Pretending otherwise does not buy a night, it spends one.
