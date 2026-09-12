# Hunger Games simulation — project handoff

## Concept

A spectator-style agent-based simulation, not a player-controlled game. Players
are rendered as dots in a pygame window. Each has strength and speed stats,
and hunger/thirst/sleep needs that must be managed. Players can acquire
weapons and loot, move around the arena with organic-but-purposeful behavior,
form and break alliances, and fight in battles that are randomly resolved but
weighted by their stats. The map itself is empty except for loot, which is
concentrated toward the center. Players do not have perfect information about
each other's locations.

Author is a complete beginner to Python and to game development, and is
building this as a learning project.

## Current status

The first two build steps are implemented and visually confirmed working.
(They predate the "Remaining build order" list below, which is numbered from
the next step onward.)

- **Step 1** — pygame window opens; N players spawn evenly spaced around a
  circle at the arena center.
- **Step 2** — players wander the arena organically: each has a persistent
  `heading` (radians) that drifts by a small random amount every frame rather
  than being re-randomized, which is what makes the movement look like a
  smooth wander instead of jitter. Speed is randomized per player. Players
  bounce off the window edges by reflecting their heading.

- **Needs** (first item of the remaining build order) — hunger, thirst and
  sleep run from 100 to 0. Each player's drain rate is the base rate from
  `NEED_SECONDS_TO_EMPTY` scaled by a random ±25% factor. A player dies the
  moment any need reaches 0 (no health system). A colored warning dot
  appears above the player for each need below 30 (hunger = orange, left;
  thirst = blue, middle; sleep = purple, right). Deaths are printed to the
  terminal for now. Test durations are short on purpose.
- **Loot** (second item of the remaining build order) — food, water and
  weapons spawn once at the start (no respawning). Players pick up items
  they touch. Food/water go into an inventory and are used automatically
  when hunger/thirst drops below 50, restoring 50. Weapons are carried but
  have no effect until combat exists.

- **AI states, vision and searching** (third item) — see `ai.py`. At the
  start each player rushes the center (`RUSH_LOOT`) or flees outward
  (`FLEE_OUTWARD`), biased by a random `aggression` (0–1). Rushing ends once
  the center is in sight with nothing left to grab; fleeing ends on reaching
  a point 280 px from the center (kept 60 px from walls). After that, each
  frame: urgent needs first — `RESTING` when sleep < 35 (until 90);
  `SEEKING` visible food/water when hunger/thirst < 40 and none is carried;
  otherwise `SEARCHING` remembered items or random points — if several are
  urgent, the lowest value wins. With no urgent need: `GATHERING` visible
  loot within carry limits (3 food, 3 water, 1 weapon), else `WANDER`.
  Players see 120 px and remember loot they have seen; they only learn an
  item is gone when they see its spot again. Steering turns at most
  0.2 rad/frame and faces the target directly within 30 px. Press **D** for
  the debug view (vision circles, state-colored dots, legend).
  Loot layout: half of each type in a tight central cluster, the rest
  spread evenly via a jittered grid. Player and loot size reduced to 4 px
  so the arena reads larger.

Nothing beyond this (combat, `HUNTING`/`AVOIDING`, alliances) is
implemented yet.

**Tuning to revisit later** — player speeds (1–3 px/frame) and need
durations are deliberately fast so test runs are short. Lower them once
the simulation speed control enhancement exists, so viewing speed and
testing speed can differ.

## Architecture

Agreed module split — see the "Remaining build order" section for what's
still empty:

| File | Status | Responsibility |
|---|---|---|
| `config.py` | Implemented (partial) | Constants only: window size, colors, player count/radius, speed range, wander turn rate. Will grow as new systems are added. |
| `player.py` | Implemented (partial) | `Player` class. Has: `id`, `x`, `y`, `speed`, `heading`, `alive`, `cause_of_death`, `needs`/`decay_rates` dicts, `move()`, `update_needs()`, `draw()`, `draw_warnings()`, `inventory`, `pick_up()`, `use_supplies()`, `can_carry()`, AI fields (`aggression`, `state`, `state_timer`, `target`, `search_point`, `known_loot`), `draw_vision()`. Still needs: `strength`, alliance membership. |
| `main.py` | Implemented | Entry point: pygame init, game loop (handle events → update → draw → clock tick), `create_starting_players()` for the circle formation. |
| `arena.py` | Implemented (partial) | `LootItem` and `Arena`: loot spawning, pickup, drawing. Wall-bounce is currently handled inline in `Player.move()` against the screen edges from `config.py` — this should likely move here once the arena boundary is distinct from the window itself. |
| `ai.py` | Implemented (partial) | Per-player decision logic / state machine. Decides movement goals, alliance proposals/betrayals. |
| `combat.py` | Empty file | Battle resolution logic. Takes players/alliance groups, returns an outcome. |
| `utils.py` | Implemented | Shared math helpers (`distance`, `angle_to`, `angle_difference`) so `ai.py` and `combat.py` don't duplicate logic. |

## Design decisions established so far

**Movement** — persistent-heading random walk, not goal-seeking yet. Speed is
currently just a random value assigned per player at spawn
(`PLAYER_MIN_SPEED`/`PLAYER_MAX_SPEED` in config) as a placeholder for the
eventual speed stat, which will need to also feed into combat flee rolls.
`heading` is wrapped to the range 0–2π every frame; when steering toward a
target, the angle difference must also be wrapped to −π…π so players turn
the short way round.

**Game loop order** — each frame runs all updates first, then draws all
players, so interactions never leave a frame half-updated on screen.

**Environment** — run with `python` (3.12, has pygame). The `py` launcher
defaults to 3.14, which has no pygame. VS Code is pointed at 3.12 in
`.vscode/settings.json`.

**AI state machine** (implemented in `ai.py`, except `HUNTING` and
`AVOIDING`, which arrive with combat) — each player gets a
`state` (e.g. `RUSH_LOOT`, `FLEE_OUTWARD`, `SEEK_WATER`, `HUNTING`,
`SEARCHING`, `RESTING`, `AVOIDING`) that determines their current movement
target. A personality trait (e.g. aggression) assigned at spawn biases the
initial rush-vs-flee choice and other decisions. Needs dropping below a
threshold should override whatever state a player is in. Alliance
formation/betrayal decisions live in this layer — `combat.py` only needs to
know two players are currently allied, it doesn't decide alliances.

**Vision and the "searching" state** (implemented) — each player has a vision radius; the AI only reacts to threats
or loot within it, which is what enforces imperfect information about other
players' locations. A dedicated `SEARCHING` state handles the case where a
player has a reason to look for something (an enemy last seen nearby, hunger
driving loot-seeking) but nothing is currently in vision: they move
purposefully toward a last-known location or plausible direction rather than
falling back to plain wander.

**Planned alliance structure** (not yet implemented) — every alliance has
one leader. The leader decides what the alliance does (its state/goal),
taking into account the shared needs of all members rather than only its
own. The other members loosely follow the leader — staying near it and
adopting its goal, while keeping some individual movement — instead of
making independent decisions.

**Planned combat resolution** (not yet implemented):
- Effective strength = own strength + a fraction of active allies' strength.
- Base win probability = `strength_A / (strength_A + strength_B)`.
- Speed determines whether the loser manages to flee instead of being
  eliminated — a separate roll, not part of the win/lose roll itself.
- The outcome should be drawn from multiple weighted categories (eliminate /
  opponent flees and drops resources / both flee / mutual resource loss), not
  a strict binary win/lose.

## Accepted enhancements (build in after core mechanics)

- Vision radius + `SEARCHING` state — folded directly into the AI design
  above, not a bolt-on.
- **Elimination feed** — a running text log of key events (eliminations,
  alliances formed/broken) for a viewer to read.
- **Visual state indicators** — dim a player's dot as hunger/thirst drops;
  tint allied players the same color.
- **Adjustable simulation speed** — pause / speed up / slow down via keypress.
  Lower priority; matters mainly for iteration speed once full runs take a
  while.
- **Post-run summary** — final rankings, kill counts, alliance history,
  shown or exported once a winner is decided.

## Explicitly rejected — do not reintroduce

- **Shrinking safe zone** (arena contracts over time). Rejected outright.
- **Care packages** (mid-run bonus loot drop events). Rejected outright.

## Remaining build order

1. ~~Needs — hunger/thirst/sleep decay over time; some way to visualize it
   (feeds into the visual state indicators enhancement).~~ Done.
2. ~~Loot — spawning and pickup in `arena.py`, weighted toward the center.~~ Done.
3. ~~AI states with real goals, including vision radius and `SEARCHING`
   (`ai.py`).~~ Done (`HUNTING`/`AVOIDING` moved to step 4).
4. Combat resolution (`combat.py`).
5. Alliances, layered on top of AI and combat. Leader-based — see
   "Planned alliance structure" above.
6. Remaining enhancements: elimination feed, visual state indicators (may
   fold into steps 1 and 3), simulation speed control, post-run summary.

Each step has been built and confirmed visually before moving to the next —
that pattern should continue.

## Working style

- Complete beginner to Python game development — wants explanations
  accompanying code, not silent code dumps.
- Wants to learn and not just produce a result. Run code by and ensure
  it is understood and productive for learning.
- Strong preference for incremental builds: confirm each stage visually
  working before moving to the next feature.
- Prefers direct, precise communication over softened or over-elaborated
  explanations.
- Prefers formal, professional tone.