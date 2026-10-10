# Choosing the bar, and building the capture harness

Read this during Phase 1–4 when the goal does not already come with an obvious
reference, or when it is not clear how to turn the work into something inspectable.

The per-domain recipes below line up with `init.py --kind`, which seeds a starter
lens set and gates for each. Those seeds are drafts — adapt them to the bar actually
chosen, or the rubric ends up grading a generic idea of quality rather than the
distance to this particular standard.

## What makes a bar a bar

Three questions. A bar that fails any of them will quietly turn the loop into
self-congratulation, because a critic that cannot look at the standard ends up
scoring intent instead of output.

1. **Can it be opened?** A file, a URL you can screenshot, a captured recording,
   a number produced by a command. "Make it look professional" is not a bar.
2. **Is it out of reach?** If we can plausibly match it in two rounds, it will not
   stop us settling. Matt Shumer used real Call of Duty screenshots for a
   browser game — the bar being unreachable is the feature, not a flaw.
3. **Does it compare like with like?** A 16:9 cinematic still is a bad bar for a
   portrait mobile screen. Match framing, aspect, and subject, or the comparison
   measures the wrong difference.

## Where bars come from, in order of preference

1. **The user handed one over** — a screenshot, a photo, a link, a competitor's
   file, "make it like that video". Use it, do not improve on it.
2. **A real-world exemplar you can capture** — the actual product, game, site, or
   artist's work being aimed at. If an in-app browser or Playwright is available,
   capture it once into `ref/` at a fixed viewport and you have
   a genuine bar. Otherwise ask for one screenshot; that is cheap for the user.
3. **A measurable ceiling** — 60fps at 4× the current object count, ≤14 LUFS,
   bundle under 200KB, zero layout shift. Numbers are the strongest bars because
   the free gates can check them every round without a critic.
4. **Your own best previous work** — a past render, a past video, the best asset
   in the project. Weaker (it drifts with taste) but real and inspectable.
5. **A generated straw-man ceiling** — if nothing external exists, produce one
   deliberately over-the-top version first, freeze it as `ref/`, and beat it. Use
   this last: it can only be as ambitious as the first attempt was.

Write the chosen bar into `BAR.md` with a one-sentence justification. One sentence,
because if it takes a paragraph to explain why this is the standard, it is not
concrete enough to compare against.

## Per-domain recipes

Each row: the bar to reach for, the capture that makes our work inspectable, the
lens rotation to freeze, and the free gates that run before any critic spends tokens.

### A whole product — game, app, site (`--kind game` / `--kind product`)

Read `references/product.md` in full before setting one of these up; this row is the
summary. The defining difference: **no single bar covers it**, so one reference file
is not enough and a screenshot bar will quietly reduce the run to a render run.

- **Bar** — one per facet, not one for the run. Gameplay video of the reference title
  (cut into a filmstrip) for the loop · input-to-response latency in ms for feel ·
  counts for content and progression (levels, cars, upgrades, hours) · a reference
  clip plus SFX-per-30s for audio · the flow screen by screen for UX · a target frame
  rate at target complexity for perf · the screenshots for the frame. Most of these
  are numbers, which makes them free gates rather than critic rounds.
- **Capture** — a scripted headless session per `play` piece: fixed seed, scripted
  inputs, fixed duration, emitting a filmstrip (frames at a fixed interval, tiled) and
  a metrics JSON (completed, duration, fps min/mean, state changes, events, score,
  deaths). Plus the ordinary screenshot script for the visual and UX pieces.
- **Lenses** — core loop · control feel · challenge & pacing · feedback · session
  shape · presentation. Presentation is one of six on purpose.
- **Gates** — everything in `DELIVERABLE.md`, re-run every round, plus boots clean,
  session completes, frame rate holds, no softlock. `next.py` will not open a quality
  round while a deliverable gate is unchecked.
- **Watch for** — the deliverable and the artifact are different things here, and the
  loop only ever protects the artifact. That asymmetry is the whole reason for
  `DELIVERABLE.md` and the vertical slice before round 1.

### Still image, render, thumbnail, sprite

- **Bar** — a real photo/screenshot/artwork at the same framing and subject.
- **Capture** — the render or export command, at the reference's aspect ratio.
- **Lenses** — silhouette (128px squint) · value structure (light vs dark masses) ·
  detail density · colour & material · cohesion (one authored thing or parts?).
- **Gates** — the export succeeds; non-empty; correct dimensions.

### 3D model from a reference image

- **Bar** — the reference photo, plus one or two extra views if available.
- **Capture** — a headless render script locked to the reference camera: same
  angle, same FOV, same crop. Freeze this script in round 0 — if the camera moves
  between rounds you cannot tell improvement from reframing.
- **Lenses** — silhouette · proportion (limb/part ratios against the reference) ·
  part count and completeness (what exists on the bar and not on ours) ·
  surface & material · readability at thumbnail size · animation-readiness
  (does the rig survive a test pose without collapsing).
- **Gates** — scene builds; no NaN transforms; poly budget; render non-blank.

### Game feel, juice, combat

- **Bar** — a recording of the game you are chasing, or your own best moment.
- **Capture** — a scripted 6–10 second clip of a fixed scenario (same spawn, same
  inputs) plus frame samples at the impact moments. Determinism matters more here
  than anywhere else, because feel is invisible in a static frame.
- **Lenses** — impact (does the hit read in one frame?) · anticipation & follow-through ·
  feedback layering (sound, shake, particles, hitstop) · readability under clutter ·
  restraint (juice that stacks into noise loses to the bar).
- **Gates** — clip records; frame rate holds; no console errors.

### UI screen, menu, HUD

- **Bar** — a screenshot of the interface being aimed at, at the same viewport.
- **Capture** — screenshot script at fixed viewport, plus one at 320px wide.
- **Lenses** — hierarchy (what does the eye hit first?) · spacing rhythm · type
  scale · state completeness (hover/empty/error/loading) · does it belong to the
  product's own visual language.
- **Gates** — renders without overflow; no horizontal body scroll; contrast ratios.

### Video, motion, montage

- **Bar** — a reference clip from the channel or studio being chased.
- **Capture** — render a short representative section, plus a frame strip every
  0.5s so motion can be judged from stills.
- **Lenses** — pacing · frame composition · transition craft · text legibility in
  motion · audio-picture sync · does the first 3 seconds hold.
- **Gates** — render completes; loudness target; no dropped frames; duration sane.

### Copy, narration, documentation

- **Bar** — a piece of writing you would be happy to have written, same genre and
  length. Diffing against a bar you admire is far more useful than a style guide.
- **Capture** — the text itself, plus a rendered view if formatting matters.
- **Lenses** — first paragraph (does it earn the second?) · claim density ·
  concreteness (specifics vs adjectives) · rhythm when read aloud · ending.
- **Gates** — length window; no placeholders left; links resolve; spellcheck.

### Spec / ТЗ, where the document is the deliverable (`--kind spec`)

- **Bar** — someone else's excellent spec for a comparable system: an RFC, a public
  API design doc, a real contractor brief. Not a template. A template tells you
  which headings to have; a real spec shows what a section looks like once it has
  actually decided something, which is the whole difference being chased.
- **Capture** — the document itself. `ab.py --squint` emits a headings-only outline
  with per-section word counts, which is the structural silhouette: a section the
  bar spends 400 words on and ours covers in 30 is a gap you can name before
  reading a sentence.
- **Lenses** — unambiguity (can a stranger read this requirement two ways?) ·
  verifiability (could a tester prove it met without asking the author?) · edge
  coverage (empty, huge, offline, concurrent, hostile) · decomposition (could two
  people build from this in parallel without colliding?) · rationale (does it say
  *why*, so a builder can resolve a case it did not foresee?).
- **Gates** — every requirement has an ID and a check; no TBD survives; every open
  question is answered; length window. Unusually strong for a document, and cheap.
- **Watch for** — self-recognition is at its worst here, since you wrote the prose.
  Score each rubric line explicitly before looking at the pair, compare section
  against matching section rather than whole documents, and this is the one domain
  where an occasional cold critic earns its cost.

### Working from screenshots

Screenshots arrive in two roles and the run breaks if they are confused, so settle
which one before anything else:

- **As the bar** ("make it like this") — someone else's product. Copy into `ref/`
  and match the capture to their framing: same viewport, same crop, same screen
  state. Comparing a 1440px marketing shot to our 390px mobile view measures the
  framing, not the work.
- **As the starting state** ("here's mine, fix it") — the user's own thing. These
  are round 0's artifact. The bar must still come from outside, or the run tops out
  at "slightly better than the screenshot I was handed". Asking for one reference
  shot costs the user thirty seconds and is what makes the rest of the run mean
  anything.

Either way, our side has to be re-captured every round, so a screenshot script is
required for an unattended run — a browser at a fixed viewport, a headless render,
an emulator capture. If the user is dropping screenshots in by hand, the loop still
works, but at their pace and not overnight.

### Code quality and performance

- **Bar** — a benchmark number, or a codebase whose module you would be happy to
  have authored. For performance the bar is always a number, which makes the free
  gates do nearly all the work.
- **Capture** — benchmark output, profile, or the module under review.
- **Lenses** — hot path cost · allocation churn · API surface (would a stranger
  misuse it?) · failure behaviour · test honesty (do the tests fail if you break it).
- **Gates** — builds; tests pass; lint; the benchmark itself.

## When the artifact cannot be captured

If you cannot produce something inspectable, the loop cannot run — a critic with
nothing to look at will grade the description of the work, which always passes.
Spend the effort on the harness instead: a screenshot script, a headless render, a
recorded clip, a benchmark command. That harness is reusable for every future
round and every future run, so it is the highest-leverage thing built all day.

If it is genuinely impossible (the output only exists in the user's head or on
their device), say so and offer the alternative: the user captures once per round
and drops the file in, and the loop runs at their pace instead.
