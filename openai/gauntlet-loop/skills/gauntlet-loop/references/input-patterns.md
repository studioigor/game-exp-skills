# Specs and screenshots as Gauntlet inputs

Read this in Phase 1 when the input is a spec/ТЗ or one or more screenshots.

## Specs

Specs show up in two opposite roles.

### A spec handed in as input

Treat it as the goal, not the bar. It says what to build, not how good the result
must be. Split it three ways:

- Resolve all ambiguities in one pass before an unattended run.
- Turn requirements into `spec_gates.md`, machine-checkable wherever possible.
- Adopt its sections as `PIECES.md` instead of inventing a second decomposition.

Choose an external bar: a real comparable product, benchmark number, or target
interface. Record the input spec path in `BAR.md` so every continuation can find it.

### A spec as the deliverable

Use `--kind spec`; the document itself is the artifact.

- Use an excellent real spec of the same class as the bar, not a template.
- Treat the rubric as primary because self-recognition weakens textual A/B blindness.
- Compare matching sections. Use `ab.py --squint` for headings and section word counts.
- Gate every requirement on an ID and check; allow no TBD or unanswered question.

When this spec wins its rotation, it may become the input goal of a separate build
run. That run needs its own external bar.

## Screenshots

First decide whether the surrounding request names a whole product. A screenshot can
grade only the visual facet; if the user asked for a game or app, use a product run
and keep screenshots as one facet's bar.

### Screenshots as the bar

For "make it like this", copy the external reference into `ref/`. Match viewport,
crop, aspect ratio, and screen state in every capture.

### Screenshots as the starting state

For "here is mine, fix it", treat the shots as round 0 artifacts. Choose a stronger
external standard; otherwise the run can only become better than its own starting
point.

In both cases recapture our side every round with a frozen browser, renderer, or
emulator command. If only the user can capture it, run at their pace rather than
claiming the run can proceed unattended.
