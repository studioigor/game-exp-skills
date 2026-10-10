# Art — the visual ceiling, and how to be unmistakable

Read this at stage 1 when writing `ART.md`, and again at every `visual` polish
round. It exists because of a specific failure: a run that treats "looks decent"
as the visual bar ships a game that looks like every other AI-built game — flat
lighting, default materials, no post-processing, nothing anyone would screenshot.

**The rule that replaces "parity with the reference": the visual bar is the
ceiling of the stack, not the floor of acceptability.** The reference screenshots
say what kind of thing this looks like; the stack says how good it is allowed to
look; the bar is both together. A `visual` facet is never *won* while the scene
has no working post-processing chain and none of the signature techniques from
`ART.md` on screen.

---

## ART.md — decided at stage 1, frozen with the pillars

Written before any code, for the same reason the pillars are: an art direction
derived from whatever got rendered is a rationalisation, not a direction. Five
sections, each one line to one paragraph:

1. **The direction, named.** One phrase with an opinion in it — "neon-noir in
   the rain", "sun-bleached Soviet seaside", "blueprint that came alive".
   "Stylised and colourful" is not a direction; it fits every mobile game ever
   made. The test: could an artist paint a key frame from the phrase alone and
   land close?
2. **Palette.** 4–6 actual hex values with roles: dominant, secondary, one
   accent that is *reserved* (the accent means something — danger, interactable,
   reward — and appears nowhere else). Write the forbidden colours too.
3. **Light.** Where it comes from, what colour it is, how hard the shadows are,
   what fog/atmosphere does. Light is 80% of a look — a grey-box scene with
   authored light already reads as the game; a textured scene under default
   ambient never does.
4. **Shape language.** What silhouettes are made of — long horizontals, brutal
   slabs, thin verticals, soft blobs — and what is deliberately absent.
5. **Three signature techniques, minimum.** The things by which a screenshot of
   this game is recognised among a hundred games of the same genre. Named
   concretely from the ceiling catalogue below, not as adjectives: "wet asphalt
   doubles every light source" is a signature; "moody atmosphere" is not.

## The creative method

- **Steal from another medium.** The reference *game* sets the genre look; the
  visual identity comes from somewhere games are not looking — a film, an album
  cover, brutalist architecture, botanical illustration, risograph print. A run
  that takes both look and feel from the same game produces a worse copy;
  cross-medium theft is the cheapest originality there is.
- **One dominant.** Pick one technique as the star; everything else supports it.
  Ten effects at 10% is mush; one at 100% plus nine quiet ones is a style. The
  dominant is usually the first signature technique.
- **The anti-generic check**, run on the finished ART.md: if this document could
  be attached to any competent game in the genre without anyone noticing, it has
  chosen nothing. Rewrite until at least one line would make a producer nervous.
- **Commit at full strength.** A bold direction applied timidly reads as a
  mistake; the same direction at full strength reads as intent. When in doubt,
  push the slider further, then let a polish round pull it back with evidence.

---

## The ceiling catalogue, per stack

What "maximum of the stack" actually contains. Stage 6 visual rounds pick from
here; a run that has used none of its stack's list is nowhere near its ceiling,
however clean the screenshot.

### Three.js / WebGL

- **Post-processing chain** (`EffectComposer` or the `postprocessing` package) —
  this single item moves a scene from "demo" to "game" more than any other:
  bloom (selective, not global glow-everything), vignette, chromatic aberration
  at the edges, film grain, color grading via LUT, SSAO for contact shadows,
  depth of field for menus and photo moments, god rays where there is a sun.
- **Light as design**: 2–3 authored lights with colour temperature contrast
  (warm key, cool fill), baked or blob shadows where real ones are too costly,
  emissive materials + bloom as the cheap "expensive look", fog (`FogExp2`) for
  depth layering — the free depth cue that beginner scenes always skip.
- **Custom shaders** where they are seen: water, heat haze, dissolve/hologram on
  spawn and death, scrolling emissive panels, fresnel rim on the player so it
  separates from the background at all times.
- **Particles with physics** (GPU or instanced): impact debris, exhaust, dust
  motes in light shafts, weather. A static world with three moving particle
  systems reads as more alive than an animated world with none.
- **Instancing** for density — a hundred lamp posts cost one draw call; density
  is a look. **Environment maps** for anything shiny; a fake studio HDRI on a
  car sells the whole frame.
- **Camera as craft**: slight FOV kick with speed, a degree or two of roll in
  turns, handheld drift at idle. The camera is a free actor; a static camera is
  a wasted one.

### Canvas 2D

- **Parallax** — 3+ depth layers minimum, including one *in front of* the action
  (foreground silhouettes at higher speed). Depth is the whole game here.
- **Light without lights**: `globalCompositeOperation` — `lighter` for glows and
  fire, `multiply` darkness with punched-out light circles for night scenes;
  radial-gradient falloffs as lamps; a full-screen gradient overlay as grade.
- **Screen-space juice**: shake with rotation (not just offset), hit-stop,
  full-screen flash at 5–10% opacity on impact, scanlines/grain overlay at low
  alpha, palette-shift on state change (heat, low health) instead of a HUD icon.
- **Trails and afterimages** via translucent clears or position history —
  movement quality for one evening of work.
- **Palette discipline is the style**: at 4–6 enforced colours, "programmer art"
  reads as intentional design. Dither gradients if the direction is retro.

### Godot 4

- **WorldEnvironment stack** — the post chain in one node: glow (with HDR
  threshold), SSAO, SSIL, volumetric fog, adjustments + color correction LUT,
  screen-space reflections. Turning these on and *tuning* them is the ceiling
  gap most Godot projects never close.
- **GPUParticles** with attractors and collision; trails for projectiles.
- **Shader materials** from Godot's shader library patterns: dissolve, outline,
  wind sway on foliage, flag wave — each is twenty lines of `.gdshader`.
- **Light nodes as art**: coloured lights with shadows on a handful of key
  objects, `CanvasModulate` + point lights for 2D night scenes.

---

## Reading a visual polish round

The lenses in RUBRIC.md say what to compare; this says what order to fix in.
Cheapest ceiling-raisers first:

1. palette + light (grade the whole frame before touching any asset);
2. post-processing chain on and tuned;
3. the dominant signature technique at full strength;
4. motion in the frame — particles, camera, idle animation, background life;
5. per-asset material and silhouette work — last, because it is per-asset.

A gap phrased "make the models better" is almost always actually gap 1 or 2 in
disguise. Assets are the most expensive fix and the least of the look.

The one honest caveat: the ceiling serves the direction, not the other way
round. An effect that fights the ART.md direction — bloom on a flat-graphic
look, film grain on a clean vector style — is a loss under the cohesion lens
even though it is "more". Maximum of the stack means every technique the
*direction* can use, at full craft.
