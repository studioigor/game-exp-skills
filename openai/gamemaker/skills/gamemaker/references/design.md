# Design — what to decide in stage 1, and what to check afterwards

Read this in full at stage 1. Come back to it whenever `next.py` prints
`DESIGN CHECK DUE`.

Everything here is cheap and structural. The checks in particular cost minutes and
catch things no lens in the rubric can ever see, because none of them are visible
in a single capture: a game can pass every visual, feel and performance lens and
still be boring for reasons that only show up when you look at all the systems at
once.

---

## 1. Pillars and anti-pillars

Three to five principles that define what this game **is**. Every design, art,
audio and code decision serves at least one. A system that serves none is scope
creep with a nice name.

A pillar earns its place only if it is:

- **falsifiable** — it makes a claim a build can contradict. "Fun combat" is not a
  pillar. "Combat rewards patience over aggression" is.
- **constraining** — if it never forces you to say no to something, it is
  decoration. Good pillars eliminate options.
- **cross-departmental** — a pillar that constrains mechanics but says nothing
  about art, audio and code is half a pillar. Real ones shape every discipline.
- **memorable** — if they cannot be recited from memory there are too many, or
  they are too complicated to be used at 3am, which is when they are needed.

### What real ones look like

| Game | Pillars | Why they work |
|---|---|---|
| God of War (2018) | Visceral combat · father-son journey · one continuous camera · Norse myth reimagined | "One continuous camera" is radical — it cut a standard cinematic tool outright. "Father-son" constrains narrative, level design **and** combat. |
| Hades | Fast fluid combat · story through repetition · every run teaches something | "Story through repetition" justified the roguelike structure narratively: death *is* the story. |
| Celeste | Tough but fair · accessibility without compromise · story and mechanics are the same thing | The last one prevented mechanics from ever being "just gameplay" — the dash *is* the anxiety. |
| Hollow Knight | Atmosphere over explanation · earned mastery · the world tells its own story | "Atmosphere over explanation" killed tutorials outright; the world had to teach through level design. |
| Dead Cells | Every weapon is viable · combat is a dance · permanent death creates meaning | "Every weapon is viable" is brutally constraining — it commits the whole project to permanent balance work. |

Notice what they have in common: each one **costs something**. A pillar you can
satisfy for free is not doing any work.

### For software rather than a game

Same test, same value. "State survives a reload." "No screen ever blocks on a
spinner." "Every error says what to do next." "Nothing is destroyed without an
undo." Each is falsifiable, each forces a no, each shapes design and code and copy.

### Anti-pillars

One or two things this game deliberately will **not** do, however tempting. They
are worth as much as the pillars because they are what an unattended decision gets
checked against — "no open-world filler driving between events" settles a hundred
3am arguments before they happen.

---

## 2. The core loop, at three scales

The nested-loop model. Each scale fails differently, so each one earns its own work
later — this is also how the `play` facet gets decomposed into more than one thing.

- **30 seconds — the micro-loop.** The action that must be satisfying *before any
  reward exists*. Steering through traffic. The swing connecting. The block
  snapping into place. If this is not good, nothing built on top of it rescues it,
  and no amount of progression disguises it.
- **5–15 minutes — the meso-loop.** Goal → effort → reward. The unit of "one
  more". A run, a match, a floor, a delivery. It needs a beginning that sets a
  target and an end that resolves it.
- **One session — the macro-loop.** What progresses, where the natural stopping
  point is, and what makes someone come back tomorrow. A game with no macro-loop
  is fun once.

A game missing any of the three has a specific, predictable complaint attached:
no micro → "it feels bad"; no meso → "it's aimless"; no macro → "I played it once".

### Three questions to ask the finished loop

Self-determination theory, reduced to what a build can answer. Ask them of the
loop as written; a "no" is a stage-1 gap, not a polish item:

- **Competence** — does the player get visibly better, and can they *see* that
  it was them? (A run won by upgrades alone fails this; skill has to show.)
- **Autonomy** — is there a real choice each cycle whose consequences the player
  owns — route, build, risk level — or is there one path walked at varying speed?
- **Relatedness/expression** — is there anything of *theirs* in the game: a
  loadout, a style, a base, a best-run ghost? Single-player games earn this
  through expression, not through other people.

---

## 3. Difficulty

### Philosophy — pick one and state it

Tuning without a stated philosophy converges on generic "balanced", which is
nobody's favourite anything.

1. **Difficulty is the product.** Overcoming it *is* the reward; reducing it
   removes the point. (Dark Souls, Celeste with assists off.)
2. **Accessible entry, opt-in depth.** The base experience is completable by most;
   challenge is available to those who want it. (Hades, Hollow Knight.)
3. **Difficulty serves narrative pacing.** Challenge rises and falls to match story
   beats — capable during resolution, threatened during crisis. (The Last of Us.)
4. **Relaxed engagement.** Challenge exists but is never the focus; failure is
   gentle and rare. (Stardew Valley, Animal Crossing.)

Then answer one more question explicitly: **what is the player allowed to feel, and
for how long, before the design must intervene?** Is frustration permitted? For one
attempt or for ten?

### Axes — do not tune only one

Most games have several independent dimensions of challenge, and tuning only
execution while another is overloaded produces a game players describe as
*confusing* rather than *hard*:

- **execution** — can you physically do it?
- **decision** — do you know which option is right?
- **resource pressure** — do you have enough?
- **time pressure** — do you have long enough?
- **information** — do you know what is happening?

For each axis: can the player reduce it through choices, builds or settings? If
not, it is a forced dimension and every use of it should be deliberate.

### The flow channel — plot it once

Sketch two curves over the first hour of play: what the game demands, and what
the player can do (skill plus unlocked power). Flow lives where demand tracks
slightly above ability; the two classic failures are visible in the sketch
before they are visible in a playtest: demand flat while ability climbs →
boredom by minute 20 (the usual fate of games tuned "fair" at minute 1), and
demand stepping up faster than ability at a difficulty spike → the churn point.
The sketch costs five minutes and turns "tune the difficulty" into "move this
segment of this curve" — and any breakpoint in it should coincide with a meta
unlock, which is what section 5e checks the arithmetic of.

---

## 4. Economy

List every resource — currency, XP, materials, stamina, health, ammo, heat — and
for each, its **sources** (faucets) and its **sinks**. Write the flow rates even as
guesses; a wrong number can be corrected, an absent one cannot.

| Condition | Sign | What the player experiences |
|---|---|---|
| Source, no sink | accumulates forever | late game becomes trivial, the resource becomes meaningless |
| Sink, no source | drains to zero | the system silently becomes unavailable |
| Source ≫ sink | surplus | rewards stop being rewards |
| Sink ≫ source | constant scarcity | grinding and gatekeeping |
| Positive feedback | more resource → easier to earn more | runaway leader, snowball, no tension |
| No catch-up | falling behind accelerates | unrecoverable states, quitting |

---

## 5. The holism checklist

Eight checks. Run them at the end of stage 1, and again whenever `next.py` prints
`DESIGN CHECK DUE`. Findings go into `open_gaps.md` — they are gaps, not blockers.

Each one is invisible to every lens in `RUBRIC.md`, because a lens looks at one
capture and these live in the relationships between systems.

### 5a. Competing progression loops

A game should have **one** dominant progression loop that players feel is the
point, with supporting loops feeding it. Scan for systems that award the primary
resource, describe themselves as "the core loop", and have comparable depth.

> combat awards XP and calls itself the core loop; crafting awards XP and calls
> itself the primary activity; exploration awards XP and calls itself the main
> driver. → Three systems claim the throne and pay the same currency. Players will
> optimise one and ignore the rest, and the game will feel like it is about
> nothing in particular.

### 5b. Attention budget

Count the systems requiring **active** decisions simultaneously during the core
loop (active = the player must decide about it regularly; passive = it runs and
they see results). More than 3–4 concurrent active systems is cognitive overload
for most players. Which of them can become passive?

### 5c. Dominant strategy

A dominant strategy makes every other strategy irrelevant: players find it, use it
exclusively, and find the rest of the game boring. Look for resource monopolies,
risk-free power (high reward *and* low risk), options with no trade-off, and any
progression choice that is "clearly correct".

> Ranged deals 80% of melee damage at zero risk. Unless melee offers something
> ranged structurally cannot — stagger, AoE, resource regain — ranged is dominant
> and half the combat design is dead weight.

### 5d. Faucets and sinks

The economy table above, applied. Every resource, both directions.

### 5e. Difficulty curve mismatch

Everything that scales with progression must scale in compatible directions and at
compatible rates. Extract what scales, how (linear, exponential, stepped) and when.

> Enemy health ×2 per area; player damage +10% per level. By area 5 enemies have
> 32× health and the player deals 1.5×. The gap widens forever.

### 5f. Pillar drift

Every system, checked against `PILLARS.md`. A system whose fantasy maps to no
pillar is scope creep by design: add a pillar that covers it, redesign it to serve
one, or cut it. Also check the **anti**-pillars — a system that does what an
anti-pillar forbids is a direct violation, not a trade-off.

### 5g. Player fantasy coherence

The fantasies across systems should reinforce one identity. "You are a ruthless
precise warrior" in combat and "you are a gentle village farmer" in the meta is
not depth, it is two games sharing a binary.

### 5h. Onboarding complexity budget

Order every concept and control by when the player *must* hold it, then check
the curve: no more than ~3 new concepts before the first meaningful success, and
each new system introduced only after the previous one has been used, not just
shown. The failure this catches is structural, not a tutorial-copy problem — if
minute one genuinely requires seven concepts, the design has no on-ramp and the
`ux/first sixty seconds` lens will lose forever no matter how the screens are
worded. Fix it here: delay a system, collapse two controls, or make something
passive at the start and active later.

---

## 6. Numbers that make good free gates

Balance checks are arithmetic, so they cost nothing and run every round. Where the
game has these, write them as `check:` commands:

- **Combat** — DPS and time-to-kill per tier; flag any option strictly better than
  all others; check whether defence can create unkillable states.
- **Progression** — plot the XP and power curves; flag dead zones (nothing
  meaningful for too long) and spikes (sudden capability jumps).
- **Loot** — expected time to each rarity tier; pity-timer arithmetic; flag any
  drop that is useless at every stage.
- **Economy** — project accumulation over a session; flag infinite loops and
  unbounded surpluses.

A number is the strongest kind of bar: it can be checked without a critic, it
cannot be argued with, and it works at 3am.

---

## 7. Genre blueprints

Proven starting shapes for stage 1 — the loop at three scales, the mvp systems
list, the axes that carry the challenge, the economy skeleton. Start from the
blueprint, then *earn the differences*: every deviation should serve a pillar,
and a design that deviates nowhere has not been designed either. Typical numeric
bars per genre live in `references/bars.md`.

### Arcade racer
- **30s** steering through traffic at the edge of control; **5–15m** one race/pursuit with a standing to win; **session** career tier or heat level advances, next unlock visible.
- **mvp systems**: vehicle physics (arcade-tuned), track loader (data), opponents/rubber-band AI, race flow (start→finish→standings), timer/score, one meta currency + upgrades.
- **axes**: execution (racing line) + risk (shortcuts, traffic, heat).
- **economy**: winnings → upgrades/unlocks; sink = next tier's entry difficulty.

### Platformer
- **30s** run-jump chained cleanly; **5–15m** one level with a secret found or missed; **session** world cleared, new mechanic unlocked.
- **mvp systems**: character controller (coyote time, buffered jump — feel is the product here), level loader (data), hazards, collectibles, checkpoints, level-complete flow.
- **axes**: execution + information (secrets); difficulty via level design, not stats.
- **economy**: collectibles → unlocks; deaths are the sink of *time*, kept cheap.

### Survival / crafting
- **30s** gather-under-threat (every gather is a small risk decision); **5–15m** one day/night or expedition cycle; **session** base tier up, new biome/recipe reachable.
- **mvp systems**: needs meters, resource nodes + respawn, crafting (recipes as data), threat source that scales at night/depth, base/storage, save.
- **axes**: resource pressure + time pressure; execution stays low.
- **economy**: the whole design *is* the faucet/sink table — write it first, the danger is always "source ≫ sink by day 3".

### Roguelike / arena
- **30s** one fight with dodge/aim decisions; **5–15m** one run, power visibly compounding; **session** meta unlock changes the *next* run's options (story-through-repetition).
- **mvp systems**: combat, enemy waves/rooms (data), in-run upgrade choice (the autonomy beat), run-end summary, meta progression, seeded generation.
- **axes**: execution + decision (build synergy); randomness bounded so a run is never dead at the draw.
- **economy**: in-run currency resets (sink = run end); meta currency drips (sink = permanent unlocks).

### Tower defense
- **30s** placing/upgrading under an incoming wave; **5–15m** one map to victory/defeat; **session** new towers/maps unlocked, harder mutators offered.
- **mvp systems**: path/grid, tower types (data — this is the variety engine), wave scheduler (data), enemy types with counters, economy of build/upgrade/sell, speed control.
- **axes**: decision (placement, counters) + resource; zero execution — do not add twitch.
- **economy**: kills → build money within a map; the classic failure is a dominant tower (holism 5c) — counters must be structural.

### Idle / management
- **30s** a purchase that visibly raises the rate; **5–15m** a decision beat (automate, prestige, reallocate); **session** an order-of-magnitude milestone or prestige reset.
- **mvp systems**: resource tick, generators (data, exponential costs), automation tier, offline progress, prestige loop, big-number formatting.
- **axes**: decision only; the challenge is allocation under exponential curves.
- **economy**: *is* the game — curve mismatch (5e) is fatal here, plot cost vs production growth before coding.

### RTS-lite / autobattler
- **30s** an econ-or-army allocation call; **5–15m** one match/battle with a readable turning point; **session** ladder tier or roster growth.
- **mvp systems**: unit roster (data), production/economy, combat resolver, one AI opponent with 2–3 readable strategies, match flow.
- **axes**: decision (build order, composition) + information (scouting); cap simultaneous active systems hard (holism 5b).
- **economy**: income vs army spend; snowball guard (5d positive-feedback row) is the design problem.
