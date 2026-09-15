# Hunger Games simulation — project handoff

## Concept

A spectator-style, agent-based simulation of the Hunger Games in pygame. 24
tributes (dots) try to survive in a large arena: they rush or flee the
cornucopia, gather supplies, manage hunger, thirst and sleep, form and break
alliances, hunt, hide and fight, while the Gamemakers and sponsors interfere.
The viewer watches; the automatic camera follows the action, an event feed
narrates it in the style of the books, and a debrief summarizes the Games.

The author is a complete beginner in Python and game development and builds
this as a learning project (see "Working style").

**Version:** 2.1 (git tag `v2.1`). Earlier tags: `v2.0`.

## Running it

- `python main.py` — use `python` (3.12, has pygame and numpy). The `py`
  launcher starts 3.14, which has no pygame.
- `python -m unittest` — automatic tests (plays several whole Games
  headless; about a minute).
- Keys in the Games: Space pause, Up/Down speed (0.25×–8×), Tab debug view,
  mouse wheel / drag / W A S D camera, F automatic camera, C whole map,
  click a tribute for its card (Esc closes).
- Debrief: 1/2/3 or Tab switch tabs, click a tribute in Standings for its
  story (A shows everyone), Enter new Games, R replay the same seed, Esc quit.

## Files

| File | Responsibility |
|---|---|
| `main.py` | Entry point. `Simulation` (one Games: `step()` advances one tick), drawing of the arena view (HUD, minimap, night overlay, cards), the play loop, and the start screen → Games → debrief loop. |
| `config.py` | Every number and color, grouped by topic. Tuning happens here. |
| `player.py` | `Player`: traits, needs, inventory, strength, speed, movement, drawing of a tribute. |
| `ai.py` | `decide()`: each tribute's state and target every frame (the priority list below). |
| `combat.py` | Fights: starting them, resolving them (win chance, outcomes, escapes, injuries), revenge after kills. |
| `alliances.py` | `Alliance`: forming, joining, merging, names, supply sharing, betrayal, breaking up. |
| `gamemakers.py` | `Gamemakers`: day/night, sponsor gifts, fires, floods, mutts, feast, shrinking arena; drawing of these and of markers. |
| `arena.py` | `Arena`: terrain (painted with numpy), cornucopia, launch plates, loot, fight markers. |
| `camera.py` | `Camera`: world↔screen conversion, manual control, automatic focus with a switch cooldown. |
| `events.py` | Event feed and history (colored by kind), counters, death markers, alliance rings. |
| `narration.py` | Long lists of book-style lines for every event, one picked at random. |
| `start_screen.py` | Names and per-tribute traits before the Games. |
| `debrief.py` | End screen with tabs: Summary (numbers, awards, chart), Standings, Story. |
| `ui.py` | Shared look: colors, fonts, panels, buttons, text. |
| `utils.py` | `distance`, `angle_to`, `angle_difference`. |
| `tests/test_simulation.py` | Headless tests of whole Games. |

## How the simulation works

### Tributes
- Each tribute has a district (two per district), strength 1–10, speed
  0.18–0.45 px/frame, and needs that drain over time (hunger 165 s, thirst
  130 s, sleep 135 s to empty, ±25% per tribute). A need at 0 kills.
- Traits (random, or chosen on the start screen):
  - **temperament** killer / balanced / coward (sets aggression),
  - **roaming** edge / normal / explorer,
  - **allies** auto / never (2–6 random "loners" per game never ally),
  - **proficiency**: a weapon (×1.6 strength holding it), fists (+4
    unarmed), survival (hunger/thirst ×0.75), stealth (seen at 70% distance,
    hides more), speed (×1.2 speed, escapes more) or tracking (senses unseen
    tributes twice as far, chases longer).
- District skills: 1 sponsor favorite, 2 +2 strength, 3 more ambushes,
  4 fishing in marsh, 5 escapes more, 7 axes +3, 11 forages food, 12 bows +3.
- Weapons are knife, spear, axe, sword or bow, each with its own strength
  bonus and reach (spear and bow attack from further away, except in the
  bloodbath). Food and water are used automatically below 50.

### A Games, start to finish
1. **Countdown** (3 s) on launch plates around the cornucopia.
2. **Bloodbath** (at least 15 s): killers and most balanced tributes rush the
   horn, grab weapons, fight (every fight is an elimination attempt) and
   team up (joining an existing group is likelier than founding one);
   cowards flee outward and cannot be attacked while fleeing. If two or more
   alliances of 3+ exist, the smallest leaves the middle once. The bloodbath
   ends when the rush is over and no fight has happened for 0.5 s.
3. **The middle of the Games**: tributes explore (drawn slightly toward the
   middle, sometimes sitting still for a while), search for food and water
   (marsh refills thirst), sleep (forest or a wall; at night non-hunters
   sleep until dawn; once asleep they stay asleep at least 8 s), and react
   to everyone they meet: ally, fight or avoid. Days last 90 s.
4. **The end**: at 8 tributes a feast at the cornucopia; at 6 the arena
   starts shrinking; at 4 the **finale** — alliances break up and everyone
   converges on the cornucopia to fight to the death.

Before the gong, the Gamemakers announce the training scores (1–12, mostly
strength; highest and lowest are logged). Tributes from Districts 1, 2 and 4
are a little likelier to ally with each other (×1.4,
`CAREER_ALLIANCE_BONUS`); an alliance founded by two of them is named "the
Careers".

### Decision order (`ai.decide`, first match wins)
0. locked in a fight → stand still; asleep and still within the minimum
   sleep time → keep sleeping (unless in danger)
1. about to collapse from lack of sleep (and not hunting/escaping) → sleep
2. Gamemaker danger (fire, flood, mutt, shrinking edge) → run
3. finale → converge and fight
4. opening rush or flight
5. backing off after a fight
6. an ally is fighting nearby → join in
7. alliance member → follow the leader (join its hunts, sleep with it)
8. committed to backing away → keep going; cautious loner hunted in forest →
   maybe hide up a tree
9. others in sight → ally, fight (hunt) or avoid
10. urgent need → sleep, food, water
11. a fight was heard → investigate or keep away
12. revenge on a district partner's killer
13. sent to the middle (quiet spell or feast)
14. lone killer → maybe set an ambush
15. collect loot in sight
16. very aggressive → track unseen tributes nearby
17. explore (or chill)

### Fights
- A hunter within reach of its prey starts a fight; both stand still for
  1.5–3.5 s. Win chance = each side's share of the combined strength (allies
  within 110 px add 80% of theirs; a chaser ×1.3; an ambusher ×1.4).
- Outcomes: elimination 80% / standoff 8% / both hurt 12%. A losing tribute
  may still escape: speed share − 0.28, lower when tired, chased or injured.
  Escaping or being hurt means dropped items and 30 s of injury.
- A kill may make the victim's district partner swear revenge; 3+ kills make
  a tribute feared.
- Nearby tributes hear fights: aggressive ones come to look, others move away.

### Alliances
- Offered face to face; chance depends on both sides' willingness (district
  partners 90%, loners never). Max 6 members. Two alliances may merge (15%).
- The strongest member leads and decides for the group using everyone's
  sight and needs; members follow closely (spreading out 3.5× further while
  the group sits, sleeps or drinks: `IDLE_SPREAD_FACTOR`), join the leader's
  hunts and every ally's fights, and share food and water. Big alliances (4+) camp near the
  cornucopia unless they left it in the opening. After the bloodbath, an
  alliance that is the only group within 350 px of the cornucopia "wins the
  middle" (`Alliance.holds_middle`, `Simulation.check_middle_holder`): it
  stays there, sleeping on the spot, living off the supplies piled there.
- Tributes very low on food or water (below 25) who remember no supplies
  within 300 px head for the cornucopia as a last resort
  (`DESPERATE_SUPPLY_THRESHOLD`, `DESPERATE_KNOWN_RANGE`).
- Names of alliance members standing close together are stacked in one
  column above the group; other tributes keep their name above their own dot
  (`main.draw_name_labels`, `NAME_STACK_DISTANCE`). When an alliance fights
  another alliance or a tribute on its own, the two sides' names stand side
  by side with "vs" between them.
- Camera lingering (`camera.LINGER_SECONDS`): after a fight or a mutt attack
  the camera stays on the spot for 0.5 s. A tribute about to die of hunger or
  thirst (below 5) is shown before anything else except an ongoing fight or
  mutt attack, and the camera stays 0.3 s after it dies
  (`CAMERA_STARVE_THRESHOLD`, `CAMERA_STARVE_LINGER_SECONDS`).
- Rare betrayals; an alliance breaks up when too few members are left, when
  only allies remain, or at the finale. Each alliance gets a name ("the
  Careers" for founders from Districts 1, 2 and 4).

### The Gamemakers and the Capitol (`gamemakers.py`)
- Day/night: night darkens the view, shortens vision and sends non-hunters to
  sleep; at nightfall the day's fallen are shown.
- Sponsor parachutes for struggling tributes (favoring kills, big alliances
  and District 1).
- Every 50–80 s near a random tribute: a fire, a flood or 2–4 mutts.
- After 45 s without a fight, some tributes are quietly sent toward the
  middle and cautious ones become a little bolder.

### What the viewer sees
- Dots in alliance colors (leader with a white ring), names with district,
  warning dots for low needs, symbols under the dot (weapon, sleep), a red
  cross when injured, a faint outline when hiding.
- Loot as shapes (food circle, water drop, weapon diamond); a pulsing ring
  around fights, a red flash when decided, a bigger flashing ring in the
  alliance's color when an alliance forms or grows, small crosses where
  tributes fell; fires, floods, mutts, parachutes and the shrinking ring.
- Automatic camera: the bloodbath zoomed out, then fights, mutt encounters,
  chases and the closest pair of tributes; it stays on each for at least 3 s
  unless it ends. Cards (top left) for the tributes or alliances being shown,
  or for a clicked tribute.
- Event feed (bottom left) with book-style lines, colored by kind; HUD (top
  right) with day, tributes alive and seed; minimap (bottom right); a
  tribute list on the right (T) with each tribute's alliance color and what
  it is doing, or "fallen"; a short headline in the top middle whenever a
  tribute falls.
- Quiet stretches (after the bloodbath, before the finale, with no fight,
  chase or mutt) play 1.5× faster; G turns this off (`FAST_FORWARD_FACTOR`).
- Cards also show a tribute's training score; sponsors favor high scores.
- Every Games has a seed; the same seed and settings replay the same Games.

## Balance (measured with headless test games before 2.1)
Games last about 3–4½ minutes; the bloodbath kills 1–10; combat causes most
deaths, hunger and thirst 1–9, the Gamemakers a few. The main levers in
`config.py`: `ESCAPE_BONUS` and `OUTCOME_WEIGHTS` (lethality),
`NEED_SECONDS_TO_EMPTY` and `LOOT_COUNTS` (starvation), `PLAYER_*_SPEED`
(pace), `ALLIANCE_CHANCE` (alliances).

## History (short)
Built step by step: window and wandering dots → needs → loot → AI states and
vision → combat → leader-based alliances → event feed → traits and finale →
large arena with camera and cornucopia start → biomes and debrief →
narration → v2.0 (Gamemakers, sponsors, day/night, district skills, weapon
types, injuries, revenge, cards, seeds, tests) → new look, trait picker,
tabbed debrief, proficiency, chilling, camera cooldown → v2.1 (minimum sleep,
alliance rings, clean-up of code, config and this document).

Ideas the user explicitly declined earlier were later requested in other
forms (the shrinking arena and sponsor gifts are now wanted features).
Biome idea offered but not chosen: rock as defensive ground.

## Requested changes for next session

No open requests.

## Working style

- Complete beginner to Python game development — wants explanations
  accompanying code, not silent code dumps.
- Wants to learn and not just produce a result.
- Prefers incremental builds, confirmed visually.
- Often asks for light testing only ("no need to test rigorously").
- Prefers direct, precise communication and a formal, professional tone.
- Commits and pushes happen when the user asks; versions are tagged when the
  user names them (v2.0, v2.1).
