import math
import random
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WORLD_WIDTH, WORLD_HEIGHT, LONERS_PER_GAME,
    BLOODBATH_END_QUIET_SECONDS,
    NUM_PLAYERS, PLAYER_COLOR, LEGEND_TEXT_COLOR, CHASE_LINE_COLOR,
    SHOWDOWN_PLAYERS, SPEED_LEVELS, RUSH_DURATION,
    COUNTDOWN_SECONDS, COUNTDOWN_TEXT_COLOR, CORNUCOPIA_COLOR, CAMERA_OPENING_ZOOM,
    MINIMAP_WIDTH, MINIMAP_BORDER, LULL_SECONDS, TERRAIN_COLORS, WIN_BANNER_SECONDS,
    DEATH_MARK_SECONDS, SELECT_RING_COLOR, SKILL_DESCRIPTIONS,
    NEED_WARNING_COLORS, FIRE_COLOR, CARD_WIDTH,
    AGGRESSION_RANGES, BIG_ALLIANCE_SIZE, LEAVE_DISTANCE, TIP_SECONDS, PROFICIENCY_DESCRIPTIONS,
    WEAPON_TYPES, TRIBUTE_PANEL_WIDTH, FAST_FORWARD_FACTOR, NAME_MIN_ZOOM, NAME_STACK_DISTANCE, CAMP_RADIUS,
)
from player import Player
from arena import Arena
from camera import Camera
from start_screen import run_start_screen
from debrief import run_debrief
from gamemakers import Gamemakers
import ai
import alliances
import combat
import events
import narration
import ui
from utils import distance, angle_to


def create_starting_players(arena, names, settings=None):
    """One player on each launch plate around the cornucopia. `settings`
    (from the start screen) can fix a player's temperament, roaming style and
    whether it ever allies; anything left on "random"/"auto" stays random."""
    players = [Player(player_id=i, x=x, y=y, name=names[i]) for i, (x, y) in enumerate(arena.plates)]
    # A few random players get the "no alliance" trait. randint includes both
    # ends; random.sample picks that many different players.
    for player in random.sample(players, random.randint(*LONERS_PER_GAME)):
        player.loner = True
    for player, choice in zip(players, settings or []):  # zip stops at the shorter list
        if choice["temperament"] != "random":
            player.temperament = choice["temperament"]
            player.aggression = random.uniform(*AGGRESSION_RANGES[player.temperament])
        if choice["roaming"] != "random":
            player.roaming = choice["roaming"]
        if choice.get("proficiency", "random") != "random":  # .get: settings saved before this option existed
            player.proficiency = choice["proficiency"]
        if choice["allies"] == "never":
            player.loner = True
    for player in players:
        player.training_score = training_score(player)
    return players


def training_score(player):
    """A training score from 1 to 12, like the Gamemakers give before the
    Games: mostly strength, plus a little for weapon or fist proficiency and
    Career training, with some luck. round() gives the nearest whole number."""
    score = player.strength + random.uniform(-1.5, 1.5)
    if player.proficiency in WEAPON_TYPES or player.proficiency == "fists":
        score += 2
    if player.skill == "training":
        score += 2
    return max(1, min(12, round(score)))


class Simulation:
    """Everything that changes while the game runs: the arena, the players
    and a few flags. step() moves the whole world forward by one tick, so
    the main loop can run it several times per frame (faster) or skip it
    (paused)."""

    def __init__(self, names, seed=None, settings=None):
        # The seed decides every random choice, so the same seed replays the
        # same Games (as long as the names and settings are the same)
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        random.seed(self.seed)
        alliances.used_names.clear()
        alliances.records.clear()
        alliances.Alliance.created = 0
        self.arena = Arena()
        self.players = create_starting_players(self.arena, names, settings)
        self.all_players = list(self.players)  # everyone, including the fallen (for the debrief)
        for player in self.players:
            ai.set_state(player, ai.WAITING)
        self.gamemakers = Gamemakers(self.arena)
        ai.dangers = self.gamemakers
        ai.night = False
        self.countdown_frames = COUNTDOWN_SECONDS * FPS  # players wait on their plates
        self.frames_since_start = 0
        self.opening_over = False   # True once the rush and flight from the cornucopia are done
        self.bloodbath_deaths = 0
        self.quiet_frames = 0       # frames in a row with no fight going on
        ai.lull_active = False      # a new game starts without a quiet spell
        self.finale_announced = False
        self.game_over = False
        self.alive_history = []     # tributes alive, once per second (for the debrief chart)
        self.bloodbath_end_frame = None
        self.alliance_sent_away = False  # True once a big alliance has left the cornucopia
        self.finale_frame = None

        print(f"Seed {self.seed}. Tributes:")
        for player in self.players:
            print(f"  {player.name:>14}: {player.temperament}, {player.roaming} "
                  f"(aggression {player.aggression:.2f}, strength {player.strength:.1f}, "
                  f"speed {player.speed:.1f})")

    def step(self):
        # The countdown: nobody moves and needs don't drop yet
        if self.countdown_frames > 0:
            self.countdown_frames -= 1
            if self.countdown_frames == 0:
                best = max(self.players, key=lambda player: player.training_score)
                worst = min(self.players, key=lambda player: player.training_score)
                events.log(narration.pick(narration.TRAINING_SCORES, best=best.name, best_score=best.training_score,
                                          worst=worst.name, worst_score=worst.training_score), "gamemaker")
                for player in self.players:
                    ai.choose_opening_state(player, self.arena)
                careers = alliances.form_careers(self.players)
                if careers is not None:
                    for member in careers.members:
                        ai.set_state(member, ai.RUSH_LOOT)  # the Careers all go for the horn
                        member.target = None
                events.log(narration.pick(narration.GAMES_BEGIN), "gamemaker")
            return
        self.frames_since_start += 1
        if self.frames_since_start % FPS == 0:
            self.alive_history.append(len(self.players))

        players = self.players  # shorter name for use below

        # Every player acts before anything is drawn, so the drawn frame
        # shows one consistent world state.
        alliances.share_supplies(players)  # allies hand over food/water first
        for player in players:
            ai.decide(player, self.arena, players)  # choose state and target
            player.move()
            player.use_supplies()     # before needs drop, so a carried item can save them
            player.update_needs()

        # Start fights where hunters reached their prey; decide finished fights
        self.arena.bloodbath = not self.opening_over  # fights starting now are bloodbath fights
        combat.handle_fights(players, self.arena)
        self.arena.update_flashes()
        self.gamemakers.update(self)  # day and night, sponsors, fires, mutts, feast, ...

        # A long quiet spell (not during the opening or the finale): some
        # random players and alliances quietly head for the middle
        if self.opening_over and len(players) > SHOWDOWN_PLAYERS and \
                self.arena.frames_since_fight >= LULL_SECONDS * FPS:
            self.arena.frames_since_fight = 0
            ai.send_to_middle(players, self.arena)
            ai.lull_active = True  # avoidant players are a little bolder until the next fight
        events.update()

        # Remove players who died this step. Everyone who falls in the same
        # step shares the same place in the standings.
        survivors = [player for player in players if player.alive]
        for player in players:
            if not player.alive:
                self.record_death(player, len(survivors))
        self.players = survivors

        # Remove dead members, replace dead leaders, handle betrayals
        alliances.update_alliances(self.players)
        events.opening = not self.opening_over  # fewer symbols around the crowded cornucopia
        if not self.opening_over:
            self.send_big_alliance_away()
        elif self.frames_since_start % FPS == 0:
            self.check_middle_holder()

        # The bloodbath ends once nobody is rushing or fleeing any more, the
        # rush has had its full time, and no fight has been going on for a moment
        self.quiet_frames = 0 if self.arena.fights else self.quiet_frames + 1
        opening_states = (ai.RUSH_LOOT, ai.FLEE_OUTWARD)
        if not self.opening_over and self.frames_since_start >= RUSH_DURATION * FPS and \
                self.quiet_frames >= BLOODBATH_END_QUIET_SECONDS * FPS and \
                not any(player.state in opening_states for player in self.players):
            self.opening_over = True
            self.bloodbath_end_frame = self.frames_since_start
            self.bloodbath_deaths = NUM_PLAYERS - len(self.players)
            events.log(narration.bloodbath_over(self.bloodbath_deaths), "gamemaker")

        if not self.finale_announced and 1 < len(self.players) <= SHOWDOWN_PLAYERS:
            self.finale_announced = True
            self.finale_frame = self.frames_since_start
            events.log(narration.pick(narration.FINALE, n=len(self.players)), "gamemaker")

        if not self.game_over and len(self.players) <= 1:
            self.game_over = True
            self.alive_history.append(len(self.players))
            if self.players:
                winner = self.players[0]
                winner.placement = 1
                events.log(narration.pick(narration.WINNER, winner=winner.name, kills=winner.kills),
                           "gamemaker")
            else:
                events.log(narration.pick(narration.NO_SURVIVORS), "gamemaker")

        # Living players pick up any loot they are touching
        self.arena.handle_pickups(self.players)

    def send_big_alliance_away(self):
        """If two or more big alliances are at the cornucopia during the
        opening, the smallest of them leaves for the outer arena, so the big
        groups don't all wipe each other out at the start. It won't camp in
        the middle afterwards either."""
        # Only once per game, and only after the groups have had a few seconds to form
        if self.alliance_sent_away or self.frames_since_start < 5 * FPS:
            return
        center_x, center_y = self.arena.center_x, self.arena.center_y
        big = {player.alliance for player in self.players
               if player.alliance is not None and len(player.alliance.members) >= BIG_ALLIANCE_SIZE
               and not player.alliance.roams}
        if len(big) < 2:
            return
        leaving = min(big, key=lambda alliance: (len(alliance.members), alliance.name))
        leaving.roams = True
        self.alliance_sent_away = True
        leader = leaving.leader
        # Head out on the side of the arena the leader is already on
        away = angle_to(center_x, center_y, leader.x, leader.y)
        point = ai.clamp_to_arena(center_x + math.cos(away) * LEAVE_DISTANCE,
                                  center_y + math.sin(away) * LEAVE_DISTANCE, 80)
        for member in leaving.members:
            if member.fight is not None:
                continue  # can't leave in the middle of a fight
            member.prey = None
            ai.set_state(member, ai.FLEE_OUTWARD)  # nobody attacks them on the way out
            member.target = ai.clamp_to_arena(point[0] + member.follow_offset[0],
                                              point[1] + member.follow_offset[1], 80)
        leader.tip_target = point  # and keep going once the flight is over
        leader.tip_timer = TIP_SECONDS * FPS
        events.log(narration.pick(narration.ALLIANCE_LEAVES, alliance=leaving.name,
                                  leader=leader.name), "alliance")

    def check_middle_holder(self):
        """Once a second after the bloodbath: if one alliance is the only group
        at the cornucopia (no other tributes near it), it has won the middle.
        It stays there, living off the supplies piled around the horn."""
        center_x, center_y = self.arena.center_x, self.arena.center_y
        near = [player for player in self.players
                if distance(player.x, player.y, center_x, center_y) <= CAMP_RADIUS]
        groups = {player.alliance for player in near}  # None stands for tributes on their own
        if len(groups) != 1 or None in groups:
            return
        holder = groups.pop()
        if holder.holds_middle or holder.roams or len(self.players) <= SHOWDOWN_PLAYERS:
            return
        if any(alliance.holds_middle for alliance in {p.alliance for p in self.players if p.alliance}):
            return  # another alliance already holds it (and is just away for a moment)
        holder.holds_middle = True
        events.log(narration.pick(narration.HOLD_MIDDLE, alliance=holder.name, leader=holder.leader.name),
                   "alliance")

    def record_death(self, player, remaining):
        """Standings, a cross where it fell, a name for the night sky and the event text."""
        player.placement = remaining + 1
        player.death_frame = self.frames_since_start
        self.gamemakers.fallen_today.append(player.name)
        events.add_marker(player.x, player.y, "death", DEATH_MARK_SECONDS)
        if player.cause_of_death == "combat":
            if player.revenge_victim:
                how = narration.pick(narration.REVENGE_DONE, killer=player.killer_name, victim=player.name)
            else:
                how = narration.kill(player.name, player.killer_name,
                                     player.killer_armed, player.died_in_bloodbath)
            kind = "kill"
        else:
            how = narration.death(player.name, player.cause_of_death)
            kind = "death"
        events.log(f"{how} {narration.remaining(remaining)}", kind)
        events.show_toast(f"{player.name} (District {player.district}) has fallen  -  {remaining} remain")


# --- Drawing -----------------------------------------------------------------

TERRAIN_EFFECTS = {  # shown in the debug legend
    "meadow": "no effect",
    "forest": "vision halved (hides players)",
    "rock": "no effect",
    "sand": "vision +30%, thirst x1.5",
    "marsh": "slow, refills thirst",
}


def draw_legend(screen, font):
    """Debug view: each state with its dot color, and what each terrain does,
    in the top-left corner."""
    y = 8
    for state, color in ai.STATE_COLORS.items():
        pygame.draw.circle(screen, color, (14, y + 7), 5)
        text = font.render(state, True, LEGEND_TEXT_COLOR)
        screen.blit(text, (26, y))  # blit = copy the rendered text onto the screen
        y += 18

    y += 6
    screen.blit(font.render("Terrain", True, LEGEND_TEXT_COLOR), (8, y))
    y += 18
    for kind, color in TERRAIN_COLORS.items():
        pygame.draw.rect(screen, color, (9, y + 2, 11, 11))
        screen.blit(font.render(f"{kind}: {TERRAIN_EFFECTS[kind]}", True, LEGEND_TEXT_COLOR), (26, y))
        y += 18


def draw_hud(screen, font, speed, paused, camera, sim, fast=False):
    """Speed, camera mode, day and key hints in the top-right corner."""
    status = "PAUSED" if paused else f"Speed {speed:g}x"  # :g drops needless decimals (2.0 -> 2)
    if fast and not paused:
        status += " (fast-forwarding a quiet moment)"
    camera_mode = "auto" if camera.auto else "manual"
    time_of_day = "night" if sim.gamemakers.night else "day"
    lines = [
        f"Day {sim.gamemakers.day} ({time_of_day})   {len(sim.players)} alive   Seed {sim.seed}",
        f"{status}   Camera: {camera_mode}",
        "Space: pause   Up/Down: speed   G: fast-forward   Tab: debug",
        "Wheel / drag / WASD: camera   F: follow   C: whole map",
        "Click a tribute: details   T: tribute list",
    ]
    width = max(font.size(line)[0] for line in lines) + 20
    ui.panel(screen, pygame.Rect(screen.get_width() - width - 6, 6, width, len(lines) * 18 + 8),
             ui.PANEL, None, radius=6, alpha=170)
    for i, line in enumerate(lines):
        # Right-align: the text's right edge sits 16 px from the window's edge
        ui.text(screen, line, font, ui.ACCENT if i == 0 else ui.TEXT,
                (screen.get_width() - 16, 10 + i * 18), "topright")


def draw_big_text(screen, font, text):
    """Large text a third of the way down the screen (countdown, winner)."""
    label = font.render(text, True, COUNTDOWN_TEXT_COLOR)
    screen.blit(label, label.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3)))


def draw_countdown(screen, big_font, sim):
    """A big 3 - 2 - 1 during the countdown, then GO! for the first second."""
    if sim.countdown_frames > 0:
        draw_big_text(screen, big_font, str(math.ceil(sim.countdown_frames / FPS)))  # ceil rounds up
    elif sim.frames_since_start < FPS:
        draw_big_text(screen, big_font, "GO!")


def draw_minimap(screen, sim, camera):
    """The whole arena in miniature (bottom-right corner): the terrain, the
    cornucopia, every player, and a rectangle showing what the camera shows."""
    width, height = screen.get_size()
    scale = MINIMAP_WIDTH / WORLD_WIDTH
    map_rect = pygame.Rect(0, 0, MINIMAP_WIDTH, int(WORLD_HEIGHT * scale))
    map_rect.bottomright = (width - 10, height - 10)
    screen.blit(sim.arena.minimap, map_rect)

    def to_map(x, y):
        """A world position as a point on the minimap."""
        return int(map_rect.x + x * scale), int(map_rect.y + y * scale)

    for x, y, _, _ in sim.gamemakers.hazards:
        pygame.draw.circle(screen, FIRE_COLOR, to_map(x, y), 6, 1)
    pygame.draw.circle(screen, CORNUCOPIA_COLOR, to_map(sim.arena.center_x, sim.arena.center_y), 3)
    for player in sim.players:
        color = player.alliance.color if player.alliance is not None else PLAYER_COLOR
        pygame.draw.circle(screen, color, to_map(player.x, player.y), 2)

    left, top = camera.screen_to_world(0, 0, screen)
    right, bottom = camera.screen_to_world(width, height, screen)
    view = pygame.Rect(to_map(left, top), (int((right - left) * scale), int((bottom - top) * scale)))
    pygame.draw.rect(screen, MINIMAP_BORDER, view.clip(map_rect), 1)
    pygame.draw.rect(screen, MINIMAP_BORDER, map_rect, 1)


def draw_night(screen, sim):
    """Darken the whole view at night (fading in at dusk and out at dawn)."""
    darkness = sim.gamemakers.darkness(sim)
    if darkness > 0:
        shade = pygame.Surface(screen.get_size())
        shade.fill((5, 10, 30))
        shade.set_alpha(darkness)
        screen.blit(shade, (0, 0))


def inspector_lines(player):
    """Everything worth knowing about one tribute, as lines of text."""
    status = "alive" if player.alive else f"fallen (place {player.placement})"
    alliance = f"{player.alliance.name} ({'leader' if player.alliance.leader is player else 'member'})" \
        if player.alliance else ("never allies" if player.loner else "none")
    weapon = player.weapon_type if player.inventory["weapon"] > 0 else "none"
    lines = [
        f"{player.name}  -  District {player.district}",
        f"Status: {status}   State: {player.state}",
        f"Traits: {player.temperament}, {player.roaming}" +
        (f", {SKILL_DESCRIPTIONS[player.skill]}" if player.skill else ""),
        f"Proficient: {PROFICIENCY_DESCRIPTIONS[player.proficiency]}",
        f"Aggression {player.aggression:.2f}   Strength {player.fighting_strength():.1f}"
        f"   Speed {player.speed:.2f}",
        f"Kills: {player.kills}   Weapon: {weapon}   Training score: {player.training_score}",
        f"Food {player.inventory['food']}   Water {player.inventory['water']}",
        f"Alliance: {alliance}",
    ]
    if player.injury_timer > 0:
        lines.append(f"Injured ({player.injury_timer // FPS} s)")
    if player.nemesis is not None and player.nemesis.alive:
        lines.append(f"Seeking revenge on {player.nemesis.name}")
    return lines


def alliance_lines(alliance):
    """The card text for an alliance: its name, style and every member."""
    title = alliance.name[0].upper() + alliance.name[1:]  # "the Wolves" -> "The Wolves" (keeps the other capitals)
    lines = [f"{title}  -  {len(alliance.members)} members",
             f"Style: {alliance.style}   Leader: {alliance.leader.name}"]
    for member in alliance.members:
        weapon = member.weapon_type if member.inventory["weapon"] > 0 else "unarmed"
        injured = ", injured" if member.injury_timer > 0 else ""
        lines.append(f"  {member.name} (D{member.district}): str {member.fighting_strength():.1f}, "
                     f"{weapon}, {member.kills} kill(s){injured}")
    return lines


def draw_card(screen, font, top, lines, player=None):
    """A card at the top left, starting at height `top`: lines of text, plus
    need bars if it is a tribute's card. Returns where the next card can start."""
    width = CARD_WIDTH
    bars = 3 * 14 if player is not None else 0
    height = 16 + len(lines) * 18 + bars
    panel = pygame.Rect(10, top, width, height)
    ui.panel(screen, panel, ui.PANEL, ui.BORDER, radius=8, alpha=225)
    y = panel.y + 8
    for i, line in enumerate(lines):
        if i == 0:
            ui.text(screen, ui.fit(line, ui.font(14, bold=True), width - 20), ui.font(14, bold=True),
                    ui.ACCENT, (panel.x + 10, y - 1))
        else:
            ui.text(screen, ui.fit(line, font, width - 20), font, ui.TEXT, (panel.x + 10, y))
        y += 18
    if player is not None:
        for name, value in player.needs.items():
            ui.text(screen, name, font, ui.MUTED, (panel.x + 10, y - 2))
            bar_width = width - 80
            pygame.draw.rect(screen, (50, 50, 50), (panel.x + 70, y + 3, bar_width, 8))
            pygame.draw.rect(screen, NEED_WARNING_COLORS[name],
                             (panel.x + 70, y + 3, int(bar_width * value / 100), 8))
            y += 14
    return panel.bottom + 8


def draw_cards(screen, font, camera, selected):
    """The clicked tribute's card; otherwise cards for whoever the automatic
    camera is showing. A tribute in an alliance is shown as its alliance's
    card (so when alliances meet or fight, both alliances are shown). Only
    living tributes get a card, so a card closes when its tribute dies."""
    if selected is not None:
        subjects = [selected]
    elif camera.auto:
        subjects = []
        for player in camera.watched:
            if not player.alive:
                continue
            subject = player.alliance if player.alliance is not None else player
            if subject not in subjects:
                subjects.append(subject)
    else:
        subjects = []
    top = 10
    for subject in subjects[:2]:  # at most two cards, so the view stays clear
        if isinstance(subject, Player):
            top = draw_card(screen, font, top, inspector_lines(subject), subject)
        else:
            top = draw_card(screen, font, top, alliance_lines(subject))


STATUS_WORDS = {  # what the tribute list says a tribute is doing
    ai.WAITING: "waiting", ai.RUSH_LOOT: "rushing", ai.FLEE_OUTWARD: "fleeing", ai.SHELTERING: "finding shelter",
    ai.RESTING: "asleep", ai.SEEKING: "foraging", ai.SEARCHING: "searching", ai.HUNTING: "hunting",
    ai.AVOIDING: "keeping away", ai.GATHERING: "gathering", ai.FOLLOWING: "with allies", ai.TRACKING: "tracking",
    ai.EXPLORING: "exploring", ai.FIGHTING: "FIGHTING", ai.INVESTIGATING: "investigating",
    ai.CONVERGING: "to the horn", ai.DRINKING: "drinking", ai.HIDING: "hiding", ai.AMBUSHING: "lying in wait",
    ai.CHILLING: "resting",
}


def draw_tribute_panel(screen, sim, top):
    """Every tribute in district order, on the right: a dot in its alliance's
    color, its name, and what it is doing (or "fallen")."""
    rows = sim.all_players
    row_height = min(15, (screen.get_height() - 180 - top - 24) // len(rows))
    if row_height < 10:
        return  # the window is too small to fit the list
    width = TRIBUTE_PANEL_WIDTH
    rect = pygame.Rect(screen.get_width() - width - 6, top, width, 26 + len(rows) * row_height)
    ui.panel(screen, rect, ui.PANEL, None, radius=6, alpha=170)
    ui.text(screen, f"Tributes  -  {len(sim.players)} of {len(rows)} alive", ui.font(12, bold=True),
            ui.ACCENT, (rect.x + 8, rect.y + 5))
    small = ui.font(11)
    for i, player in enumerate(rows):
        middle = rect.y + 24 + i * row_height + row_height // 2
        if player.alive:
            dot = player.alliance.color if player.alliance is not None else PLAYER_COLOR
            status = STATUS_WORDS.get(player.state, "")
            if player.injury_timer > 0:
                status += ", hurt"
            name_color, status_color = ui.TEXT, (ui.RED if player.state == ai.FIGHTING else ui.MUTED)
        else:
            dot, status, name_color, status_color = (80, 80, 86), "fallen", (110, 110, 118), (110, 110, 118)
        pygame.draw.circle(screen, dot, (rect.x + 13, middle), 3)
        # Default names like "D3 Boy" already say the district; others get it in front
        prefix = f"D{player.district} "
        label = player.name if player.name.startswith(prefix) else prefix + player.name
        ui.text(screen, ui.fit(label, small, 100), small, name_color, (rect.x + 22, middle), "midleft")
        ui.text(screen, ui.fit(status, small, 80), small, status_color, (rect.right - 8, middle), "midright")


def draw(screen, fonts, sim, camera, debug, speed, paused, selected=None, fast=False, show_list=True):
    font, big_font, name_font, banner_font = fonts
    sim.arena.draw(screen, camera)  # terrain, cornucopia, plates, loot, fight markers
    sim.gamemakers.draw(screen, camera)  # fires, floods, mutts, parachutes, markers

    def on_screen(x, y):
        return camera.world_to_screen(x, y, screen)

    if debug:
        for player in sim.players:
            player.draw_vision(screen, camera)
            # Line from each alliance member to its leader
            if player.alliance is not None and player.alliance.leader is not player:
                leader = player.alliance.leader
                pygame.draw.line(screen, player.alliance.color,
                                 on_screen(player.x, player.y), on_screen(leader.x, leader.y))
    # Faint line from each hunter to the player it is chasing
    for player in sim.players:
        if player.state == ai.HUNTING and player.prey is not None and player.prey.alive:
            pygame.draw.line(screen, CHASE_LINE_COLOR,
                             on_screen(player.x, player.y), on_screen(player.prey.x, player.prey.y))
    for player in sim.players:
        player.draw(screen, camera, name_font, debug, draw_name=False)
    draw_name_labels(screen, camera, sim.players, name_font, sim.arena.fights)
    if selected is not None and selected.alive:
        pygame.draw.circle(screen, SELECT_RING_COLOR, on_screen(selected.x, selected.y), camera.size(9, 7), 1)

    draw_night(screen, sim)
    sim.gamemakers.draw_fallen(screen, font)
    draw_countdown(screen, big_font, sim)
    if sim.game_over:
        draw_big_text(screen, banner_font, f"{sim.players[0].name} wins!" if sim.players else "No victor")
    if debug:
        draw_legend(screen, font)
    events.draw(screen, font)
    draw_hud(screen, font, speed, paused, camera, sim, fast)
    draw_minimap(screen, sim, camera)
    if show_list:
        draw_tribute_panel(screen, sim, 114)
    if not debug:  # the debug legend uses the same corner
        draw_cards(screen, font, camera, selected)
    events.draw_toast(screen, ui.font(15, bold=True))
    pygame.display.flip()


def draw_name_labels(screen, camera, players, name_font, fights=()):
    """Names above the tributes. When members of an alliance stand close
    together, their names are stacked above the group instead of being drawn
    on top of each other. Everyone else keeps their name above their own dot."""
    if camera.zoom < NAME_MIN_ZOOM:
        return
    visible = screen.get_rect().inflate(40, 40)
    labeled = [(player, player.label_anchor(camera, screen)) for player in players]
    labeled = [(player, anchor) for player, anchor in labeled if visible.collidepoint(anchor)]

    # Put tributes whose labels would be close into the same group. `leader[i]`
    # points toward the group tribute i belongs to; following the pointers
    # until one points to itself finds the group. Joining two groups is just
    # pointing one at the other, so chains of close tributes end up together.
    leader = list(range(len(labeled)))

    def group_of(i):
        while leader[i] != i:
            i = leader[i]
        return i

    for i, (first_player, first) in enumerate(labeled):
        for j in range(i + 1, len(labeled)):
            second_player, second = labeled[j]
            if first_player.alliance is None or first_player.alliance is not second_player.alliance:
                continue  # only allies' names are stacked
            if abs(first[0] - second[0]) < NAME_STACK_DISTANCE and abs(first[1] - second[1]) < NAME_STACK_DISTANCE:
                leader[group_of(i)] = group_of(j)
    groups = {}
    for i, item in enumerate(labeled):
        groups.setdefault(group_of(i), []).append(item)  # setdefault: start an empty list the first time
    group_by_player = {player: group for group in groups.values() for player, _ in group}

    # An alliance fighting another alliance or a tribute on its own: the two
    # sides' names side by side, with "vs" in between
    drawn = []  # groups already drawn
    for fight in fights:
        first, second = fight.attacker, fight.defender
        if first.alliance is None and second.alliance is None:
            continue  # two tributes on their own: their names are already apart
        if first.alliance is second.alliance:
            continue  # allies (a betrayal just happened): nothing to put side by side
        left, right = group_by_player.get(first), group_by_player.get(second)
        if left is None or right is None or any(group is left or group is right for group in drawn):
            continue
        drawn += [left, right]
        middle_x = camera.world_to_screen(fight.x, fight.y, screen)[0]
        bottom = min(anchor[1] for _, anchor in left + right)
        half_width = max(player.label(name_font).get_width() for player, _ in left + right) / 2
        draw_name_stack(screen, left, middle_x - half_width - 14, bottom, name_font)
        draw_name_stack(screen, right, middle_x + half_width + 14, bottom, name_font)
        row_height = left[0][0].label(name_font).get_height() + 1
        ui.text(screen, "vs", ui.font(12, bold=True), ui.ACCENT,
                (middle_x, bottom - max(len(left), len(right)) * row_height / 2), "center", shadow=True)

    for group in groups.values():
        if not any(group is done for done in drawn):
            x = sum(anchor[0] for _, anchor in group) / len(group)  # above the middle of the group
            bottom = min(anchor[1] for _, anchor in group)           # above its highest tribute
            draw_name_stack(screen, group, x, bottom, name_font)


def draw_name_stack(screen, group, x, bottom, name_font):
    """The names of a group, alphabetically, stacked upward from `bottom`, centered on `x`."""
    for i, (player, _) in enumerate(sorted(group, key=lambda item: item[0].name)):
        label = player.label(name_font)
        screen.blit(label, label.get_rect(midbottom=(x, bottom - i * (label.get_height() + 1))))


def is_quiet(sim, camera):
    """True when nothing much is happening: after the bloodbath and before
    the finale, with no fight, chase or mutt anywhere."""
    if not sim.opening_over or sim.finale_announced or sim.arena.fights or sim.gamemakers.mutts:
        return False
    return not any(player.state in (ai.HUNTING, ai.SEARCHING) and player.prey is not None
                   for player in sim.players)


def tribute_at(sim, camera, screen, position):
    """The living tribute under a screen position (within a few pixels), or None."""
    world_x, world_y = camera.screen_to_world(*position, screen)
    closest = min(sim.players, default=None,
                  key=lambda player: distance(player.x, player.y, world_x, world_y))
    if closest is not None and distance(closest.x, closest.y, world_x, world_y) * camera.zoom <= 15:
        return closest
    return None


# --- Running the Games -----------------------------------------------------

def play(screen, clock, names, settings=None, seed=None):
    """Run one Games from the countdown until shortly after the winner is
    known. Returns the finished Simulation (for the debrief), or None if the
    window was closed."""
    fonts = (
        ui.font(13),              # HUD, legend, cards and event feed
        ui.font(90, bold=True),   # countdown
        ui.font(10, bold=True),   # names above heads
        ui.font(52, bold=True),   # winner banner
    )
    events.reset()
    sim = Simulation(names, seed, settings)
    camera = Camera(sim.arena.center_x, sim.arena.center_y, CAMERA_OPENING_ZOOM)
    debug = False
    paused = False
    speed_index = SPEED_LEVELS.index(1)  # start at normal speed
    step_budget = 0.0  # simulation steps owed; lets speeds below 1 skip frames
    frames_after_end = 0  # frames the winner banner has been shown
    selected = None       # the tribute shown in the inspector panel
    show_list = True      # the tribute list on the right (T)
    fast_forward = True   # speed through quiet moments (G)
    press_position = None # where the left mouse button went down (to tell clicks from drags)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                debug = not debug
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                paused = not paused
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                speed_index = min(speed_index + 1, len(SPEED_LEVELS) - 1)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_DOWN:
                speed_index = max(speed_index - 1, 0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                selected = None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_t:
                show_list = not show_list
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_g:
                fast_forward = not fast_forward
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    press_position = event.pos
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and press_position:
                    moved = distance(*press_position, *event.pos)
                    if moved < 5:  # a click, not a drag: select (or deselect) a tribute
                        selected = tribute_at(sim, camera, screen, event.pos)
                    press_position = None
                camera.handle_event(event, screen)

        speed = SPEED_LEVELS[speed_index]
        fast = fast_forward and is_quiet(sim, camera)  # skip through quiet moments faster
        if not paused and not sim.game_over:  # once there is a winner, the arena freezes
            # E.g. at speed 4 the budget grows by 4 each frame, so step() runs
            # 4 times; at 0.5 it grows by 0.5, so step() runs every other frame.
            step_budget += speed * (FAST_FORWARD_FACTOR if fast else 1)
            while step_budget >= 1:
                sim.step()
                step_budget -= 1

        if selected is not None and not selected.alive:
            selected = None  # the clicked tribute died: close its card
        camera.update(sim, screen)
        draw(screen, fonts, sim, camera, debug, speed, paused, selected, fast, show_list)
        clock.tick(FPS)

        # Show the winner for a few seconds, then move on to the debrief
        if sim.game_over:
            frames_after_end += 1
            if frames_after_end >= WIN_BANNER_SECONDS * FPS:
                return sim


def main():
    pygame.init()
    # RESIZABLE lets you drag the window's edges; everything adapts
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Hunger Games Simulation")
    clock = pygame.time.Clock()

    names = None     # the first start screen uses the default names...
    settings = None  # ...and random traits
    seed = None      # None = a new random seed
    while True:
        if seed is None:
            result = run_start_screen(screen, clock, names, settings)
            if result is None:  # window closed on the start screen
                break
            names, settings = result
        sim = play(screen, clock, names, settings, seed)
        if sim is None:    # window closed during the Games
            break
        choice = run_debrief(screen, clock, sim)
        if choice == "quit":
            break
        # "replay": the same Games again (same seed); "again": new Games
        seed = sim.seed if choice == "replay" else None

    pygame.quit()


if __name__ == "__main__":
    main()
