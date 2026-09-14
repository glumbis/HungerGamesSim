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
  loot within carry limits (3 food, 3 water, 1 weapon), else wander
  (since replaced by `EXPLORING`, see below).
  Players see 80 px (originally 120) and remember loot they have seen; they only learn an
  item is gone when they see its spot again. Steering turns at most
  0.2 rad/frame and faces the target directly within 30 px. Press **D** (now **Tab**) for
  the debug view (vision circles, state-colored dots, legend).
  Loot layout: half of each type in a tight central cluster, the rest
  spread evenly via a jittered grid. Player and loot size reduced to 4 px
  so the arena reads larger.

- **Combat** (fourth item) — see `combat.py` and `ai.py`. Strength is 1–10
  per player, +5 while carrying a weapon. When a player first sees another,
  it chooses once to fight or avoid it (chance to fight = its aggression,
  halved if the other is armed and it is not); the choice lasts while the
  other stays in sight. Resting players are asleep: they see nothing and
  are always attacked by anyone who sees them. Hunters chase their prey,
  search its last-seen spot if it leaves sight, and give up after 10 s
  (then 5 s without starting a hunt, avoiding instead). A fight starts
  when a hunter touches its prey. Winner chance = share of combined
  strength. Outcome weights: elimination 60% (the loser escapes with
  chance = share of combined speed + 0.2, max 0.9, dropping half its
  items; otherwise it is eliminated and drops everything), standoff 20%,
  mutual loss 20% (each drops one item). If both survive, they back off
  for 3 s and cannot fight meanwhile. Players ignore items they dropped.
  Fights show a red ring and print to the terminal; the last player
  standing is announced. Vision reduced to 80 px.
  `decide()` priority: opening phase → post-fight retreat → react to
  players in sight → urgent needs → gathering → wander. An urgent need
  cancels a hunt whose prey is out of sight.

- **Alliances** (fifth item) — see `alliances.py`. When a player on its
  own or an alliance leader first sees a non-ally, they may team up before
  choosing fight/avoid: chance = 0.6 × (1 − own aggression) × (1 − the
  other side's aggression; an alliance answers through its leader). Max 4
  members; alliances never merge; former allies never ally again. The
  strongest member leads (re-chosen if the leader dies). The leader decides
  using the group's combined vision and memory and the group's needs (rest
  if anyone's sleep is low; seek food/water if anyone is low and nobody
  carries it). Members follow the leader (distances since tightened, see
  "Alliance unity" below), join the leader's hunts and sleep beside it.
  Allies within 40 px share food/water. A leader moves at its slowest
  member's speed (half that while calm and a member is more than 45 px
  away). Betrayal: 0.3 per minute × aggression; the
  betrayer attacks the nearest former ally. An alliance breaks up below 2
  members, or when only its members are left. Normal view: members in the
  alliance color, leader with a white ring. Debug view: member-to-leader
  lines and the `FOLLOWING` state. Events are printed to the terminal.

- **Alliance unity and movement style** (refinement after alliances) —
  members keep ~16 px from their leader and gather loot only within 45 px
  of it; following members match the leader's sprint speed. If any member
  fights and survives, the whole group backs off for 3 s behind its leader
  (waking a sleeping group), after which the leader resumes the chase
  against that opponent. Anyone seen hunting a member becomes the group's
  target. Members join a chase only while the leader is actively hunting.
  Hunters wait 20 px from prey that cannot be attacked yet instead of
  standing on it. Allies within 60 px add 50% of their strength in fights.
  Idle players are `EXPLORING`: they walk to one of the nearest unvisited
  150 px cells and pause 0.5–2 s on arrival (searching for food/water also
  uses unvisited cells). The random-walk `WANDER` state is gone; a player
  without a target stands still. Speed multipliers by state: hunting and
  avoiding 1.5×, rush and flee 1.3×, seeking 1.2×, everything else 1.0×.
  Tired players first walk to a spot 40 px from the nearest wall
  (`SHELTERING`), then rest. A faint red line joins each hunter to its prey
  in both views. Measured over 5 seeds: member–leader distance median
  14–15 px; 45–64 fights per run, 66–85% with ally support; combat causes
  ~30% of deaths, thirst ~50%.

- **Alliance tuning, tracking and event feed** — alliance chance =
  0.2 × (1 − own aggression) × (1 − other side's aggression), offered only
  face to face (a group member within 80 px of the other player) and only
  once per pair of players per game. A group's fight chance = leader
  aggression + 0.2 per extra member (halved against an armed opponent if
  nobody in the group is armed). Alliance members notice non-allies within
  150 px (loners: 80 px). Alliances back off only 1 s after a fight
  (loners: 3 s). Hunters wait 20 px away while either side is still backing
  off. `TRACKING`: an alliance with fight chance ≥ 0.6 heads toward the
  nearest non-ally within 350 px via estimated waypoints (120 px ahead,
  ±0.5 rad error, re-estimated every 2 s). Fight outcome weights:
  elimination 75%, standoff 10%, mutual loss 15%; escape bonus 0.05.
  `events.py`: on-screen feed in the bottom-left corner (newest 6 events,
  10 s each, fading out) of deaths, eliminations, alliance events and the
  winner, with simulation timestamps; detailed fight lines stay in the
  terminal. Measured over 5 seeds: 3–9 alliance events per run, 22–32% of
  player time spent in alliances, `HUNTING` 8–13% of time, combat causes
  20–23 of 24 deaths, games end between 2:00 and 3:53.

- **Personality traits, alliance styles, showdown, speed control** — each
  player gets a fixed `temperament` (killer 20% / balanced 55% / coward
  25%; aggression drawn from 0.8–1 / 0.2–0.8 / 0–0.2) and `roaming` (edge
  25% / normal 50% / explorer 25%). Killers always rush at the start,
  always choose to fight (even armed opponents) and track unseen players.
  Cowards always flee at the start and always avoid; they still attack
  sleeping players, but go back to avoiding once those wake. Balanced
  players use the aggression-based rules. Edge dwellers flee to the wall
  and explore points 25–70 px from walls; explorers pick any unvisited
  cell and pause 40% as long; searching for food/water always looks
  nearby. Willingness to ally: killers 0.3, cowards 1.0, balanced
  1 − aggression. Alliance `style` is set by the founders: a killer →
  bloodthirsty (always fights, tracks); two cowards → defensive (always
  avoids, still defends members); otherwise opportunist. Showdown at ≤ 4
  players left: alliances disband, everyone hunts the nearest player with
  full knowledge of positions, and every fight is an elimination with no
  escape. `main.py` now has a `Simulation` class; Space pauses and Up/Down
  set 0.25×–8× (simulation steps per frame), shown top-right. Needs ~13%
  faster (hunger 65 s, thirst 52 s, sleep 78 s). Traits are printed to the
  terminal at the start. Measured over 5 seeds: showdown at 1:28–1:51,
  games end at 1:31–1:52, combat causes 19–23 of 24 deaths, edge dwellers
  explore at a median 52–68 px from the nearest wall vs 114–188 px for
  others.

- **Large arena, camera and cornucopia start** — world 2400×1800 (window
  1000×700, resizable). `camera.py`: automatic mode (cornucopia during the
  opening, then follows a chase framing hunter and prey, otherwise fits all
  living players) and manual control (mouse wheel zoom, left-drag,
  W/A/S/D, F = automatic, C = whole map); minimap bottom-right. Debug view
  moved from D to **Tab**. Opening: 3-second countdown on 24 launch plates
  around a golden cornucopia; 80% of weapons and 30% of food/water piled at
  its mouth; balanced players rush with chance aggression + 0.25; rushers
  grab weapons first; armed rushers (and killers once at the horn) attack
  the nearest player within 80 px; unarmed rushers flee only when hunted.
  The feed announces the start and the end of the bloodbath.
- **Slower, deadlier pace, names and simpler terrain** — speeds
  0.6–1.6 px/frame; needs hunger 140 s / thirst 115 s / sleep 75 s; rest
  below 50 sleep; shelter walk at most 300 px; loot 25 food / 30 water /
  12 weapons. Fights last 1–3 s (`combat.Fight`: both fighters locked in
  place, pulsing ring); outcome weights 85/5/10; escape bonus −0.15, and
  escape chance × (0.3 + 0.7 × stamina). A fight alerts players within
  350 px for 8 s: fight chance ≥ 0.5 → `INVESTIGATING`, otherwise move
  away. Stamina: sprinting empties it in 4 s, it recovers in 8 s; hunters
  give up after 6 s. Finale at ≤ 6 players (`SHOWDOWN_PLAYERS`): alliances
  disband, everyone is `CONVERGING` on the cornucopia, attacks anyone in
  vision or within 250 px of the horn, and fights are to the death.
  Terrain: 16 zones (meadow/forest/rock/sand/marsh), each spot taking the
  type of its nearest zone center, worked out on a 10 px grid and smoothed;
  visual only. `start_screen.py`: edit the 24 names by district; defaults
  use the tributes named in book 1 (Glimmer, Cato, Clove, Foxface, Thresh,
  Rue, Peeta, Katniss) and labels like "D3 Boy" for the rest. Names are
  drawn above heads (zoom ≥ 0.7) and used in the feed and terminal.
  Measured over 5 seeds: games end at 2:41–3:35, finale at 2:24–3:15,
  27–33 fights per game, 1–6 deaths from needs, longest chase ≤ 8.2 s.

- **Biomes, detailed map, camera, pacing and debrief** — terrain is painted
  at full resolution with numpy: 22 zones with wavy borders and a soft
  blotch texture (`Arena.paint_terrain`, `terrain_at`, `find_terrain`).
  Effects: forest halves seeing distance if either player is in it (tired
  players look for forest to sleep in within 300 px, cowards 600 px); marsh
  slows movement to 60% and refills thirst (thirsty players walk to marsh
  within 700 px and are `DRINKING` until thirst reaches 90); sand drains
  thirst 1.5× faster and extends seeing distance by 30%; rock and meadow
  have no effect. World 2800×2100; speeds 0.45–1.15 px/frame; vision 65 px;
  player and loot size 3 px. Exploring picks destinations at least 600 px
  away (explorers 1000 px). Lull alerts: after 45 s without a fight,
  aggressive loners and leaders are shown the nearest non-ally and head
  there for up to 25 s. Fights are heard within 300 px; only players with
  fight chance ≥ 0.7 investigate. A player backing away commits to it for
  2 s (stops jiggling at the edge of vision). Sleep below 20 → the player
  collapses and sleeps on the spot until 90 (no more sleep deaths). Camera:
  follows a fight until it is decided plus 0.5 s (zoom 2.4), then chases,
  otherwise the two closest non-allied players. Alliances: chance 0.35,
  max 5 members; allies within 80 px add 80% of their strength. Bloodbath
  (opening only): every fight is an elimination attempt and the escape
  chance is multiplied by 0.15; lone rushers form a new alliance 20% of the
  time but join an existing one 70% of the time; rush bias 0.15; the rush
  (and so the bloodbath) lasts at least 11 s. General
  escape bonus −0.20. End of game: the arena freezes, the winner's name is
  shown for 4 s, then `debrief.py` shows stats, standings (placement,
  district, kills, fate, time) and the scrollable event history; Enter
  starts new Games with the same names, Esc quits. Measured over 5 seeds:
  games end at 3:00–4:19, bloodbath 1–7 deaths, opening alliances reach
  5 members, no sleep deaths.

All planned features, including the post-run summary (the debrief), are
implemented.

**Tuning to revisit later** — player speeds (1–3 px/frame) and need
durations are deliberately fast so test runs are short. Speed control now
exists (Space / Up / Down), so these can be lowered for viewing without
slowing down testing. Needs have since been retuned (hunger 140 s,
thirst 115 s, sleep 75 s); games currently end at about 3:00–4:20. Combat currently causes about 15–21 of 24
deaths (5 test seeds, escape bonus −0.20) — about the level once judged to
be too many fights. `ESCAPE_BONUS`, `OUTCOME_WEIGHTS` and
`ALLIANCE_RETREAT_SECONDS` in `config.py` are the main levers.

## Architecture

Agreed module split — see the "Remaining build order" section for what's
still empty:

| File | Status | Responsibility |
|---|---|---|
| `config.py` | Implemented (partial) | Constants only: window size, colors, player count/radius, speed range, wander turn rate. Will grow as new systems are added. |
| `player.py` | Implemented (partial) | `Player` class. Has: `id`, `x`, `y`, `speed`, `heading`, `alive`, `cause_of_death`, `needs`/`decay_rates` dicts, `move()`, `update_needs()`, `draw()`, `draw_warnings()`, `inventory`, `pick_up()`, `use_supplies()`, `can_carry()`, AI fields (`aggression`, `state`, `state_timer`, `target`, `search_point`, `known_loot`), `draw_vision()`, combat/hunting fields (`strength`, `kills`, `killer_id`, `reactions`, `prey`, `prey_last_seen`, `hunt_timer`, `hunt_cooldown`, `retreat_timer`, `retreat_from`). Alliance fields (`alliance`, `former_allies`, `follow_offset`, `visible_loot`, `visible_players`), `fighting_strength()`, `current_speed()`, traits (`temperament`, `roaming`), exploring/tracking fields. |
| `main.py` | Implemented | Entry point: `create_starting_players()` (circle formation), `Simulation` class (`step()` advances the world one tick), drawing (`draw()`, legend, HUD), and the main loop with pause/speed keys. |
| `arena.py` | Implemented (partial) | `LootItem` and `Arena`: terrain background, cornucopia and launch plates, loot spawning/pickup, fights in progress and fight markers, drawing through the camera. Wall-bounce is currently handled inline in `Player.move()` against the screen edges from `config.py` — this should likely move here once the arena boundary is distinct from the window itself. |
| `ai.py` | Implemented (partial) | Per-player decision logic / state machine. Decides movement goals, alliance proposals/betrayals. |
| `combat.py` | Implemented | Battle resolution logic. Takes players/alliance groups, returns an outcome. |
| `alliances.py` | Implemented | `Alliance` class (members, leader, color), forming/joining, supply sharing, betrayal, breakups. |
| `events.py` | Implemented | Event feed: `log()` prints and stores timestamped events, `update()` expires them, `draw()` shows them bottom-left. |
| `camera.py` | Implemented | `Camera`: world↔screen conversion, zoom limits, manual control (wheel, drag, WASD, F, C), automatic focus (opening, chases, all players). |
| `start_screen.py` | Implemented | Start screen for editing the 24 tribute names before the Games. |
| `debrief.py` | Implemented | End-of-game debrief: winner, stats, standings, scrollable event history; Enter = new Games, Esc = quit. |
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

**AI state machine** (implemented in `ai.py`) — each player gets a
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

**Alliance structure** (implemented in `alliances.py` and `ai.py`) — every alliance has
one leader. The leader decides what the alliance does (its state/goal),
taking into account the shared needs of all members rather than only its
own. The other members loosely follow the leader — staying near it and
adopting its goal, while keeping some individual movement — instead of
making independent decisions.

**Combat resolution** (implemented in `combat.py`):
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
4. ~~Combat resolution (`combat.py`).~~ Done, including `HUNTING`/`AVOIDING`.
5. ~~Alliances, layered on top of AI and combat.~~ Done (leader-based — see
   "Alliance structure" above).
6. Remaining enhancements: ~~elimination feed~~ (done, `events.py`),
   ~~visual state indicators~~ (done: warning dots, alliance colors, leader
   rings, debug view), ~~simulation speed control~~ (done),
   ~~post-run summary~~ (done, `debrief.py`).

Each step has been built and confirmed visually before moving to the next —
that pattern should continue.

## Requested changes for next session

No open requests. The most recent rounds are implemented (see "Biomes,
detailed map, camera, pacing and debrief" under Current status). The user
agreed that games may stay around 3–4 minutes. Biome effects that were
offered but not chosen: rock as defensive ground (fight bonus, safer
sleep) — only add if the user asks.

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