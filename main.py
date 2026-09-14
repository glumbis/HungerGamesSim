import math
import random
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WORLD_WIDTH, WORLD_HEIGHT, LONERS_PER_GAME,
    BLOODBATH_END_QUIET_SECONDS,
    NUM_PLAYERS, PLAYER_COLOR, LEGEND_TEXT_COLOR, CHASE_LINE_COLOR,
    SHOWDOWN_PLAYERS, SPEED_LEVELS, HUD_TEXT_COLOR, RUSH_DURATION,
    COUNTDOWN_SECONDS, COUNTDOWN_TEXT_COLOR, CORNUCOPIA_COLOR, CAMERA_OPENING_ZOOM,
    MINIMAP_WIDTH, MINIMAP_BORDER, LULL_SECONDS, TERRAIN_COLORS, WIN_BANNER_SECONDS,
    DEATH_MARK_SECONDS, PANEL_COLOR, PANEL_BORDER, SELECT_RING_COLOR, SKILL_DESCRIPTIONS,
    NEED_WARNING_COLORS, FIRE_COLOR,
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
from utils import distance


def create_starting_players(arena, names):
    """One player on each launch plate around the cornucopia."""
    players = [Player(player_id=i, x=x, y=y, name=names[i]) for i, (x, y) in enumerate(arena.plates)]
    # A few random players get the "no alliance" trait. randint includes both
    # ends; random.sample picks that many different players.
    for player in random.sample(players, random.randint(*LONERS_PER_GAME)):
        player.loner = True
    return players


class Simulation:
    """Everything that changes while the game runs: the arena, the players
    and a few flags. step() moves the whole world forward by one tick, so
    the main loop can run it several times per frame (faster) or skip it
    (paused)."""

    def __init__(self, names, seed=None):
        # The seed decides every random choice, so the same seed replays the
        # same Games (as long as the names and settings are the same)
        self.seed = seed if seed is not None else random.randrange(1_000_000)
        random.seed(self.seed)
        alliances.used_names.clear()
        alliances.records.clear()
        alliances.Alliance.created = 0
        self.arena = Arena()
        self.players = create_starting_players(self.arena, names)
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
                for player in self.players:
                    ai.choose_opening_state(player, self.arena)
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

    def record_death(self, player, remaining):
        """Standings, a cross where it fell, a name for the night sky and the event text."""
        player.placement = remaining + 1
        player.death_frame = self.frames_since_start
        self.gamemakers.fallen_today.append(player.name)
        events.add_marker(player.x, player.y, "death", DEATH_MARK_SECONDS)
        if player.cause_of_death == "combat":
            if getattr(player, "revenge_victim", False):
                how = narration.pick(narration.REVENGE_DONE, killer=player.killer_name, victim=player.name)
            else:
                how = narration.kill(player.name, player.killer_name,
                                     player.killer_armed, player.died_in_bloodbath)
            kind = "kill"
        else:
            how = narration.death(player.name, player.cause_of_death)
            kind = "death"
        events.log(f"{how} {narration.remaining(remaining)}", kind)


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


def draw_hud(screen, font, speed, paused, camera, sim):
    """Speed, camera mode, day and key hints in the top-right corner."""
    status = "PAUSED" if paused else f"Speed {speed:g}x"  # :g drops needless decimals (2.0 -> 2)
    camera_mode = "auto" if camera.auto else "manual"
    time_of_day = "night" if sim.gamemakers.night else "day"
    lines = [
        f"Day {sim.gamemakers.day} ({time_of_day})   {len(sim.players)} alive   Seed {sim.seed}",
        f"{status}   Camera: {camera_mode}",
        "Space: pause   Up/Down: speed   Tab: debug",
        "Wheel / drag / WASD: camera   F: follow   C: whole map",
        "Click a tribute: details",
    ]
    for i, line in enumerate(lines):
        text = font.render(line, True, HUD_TEXT_COLOR)
        # Right-align: start the text its own width away from the right edge
        screen.blit(text, (screen.get_width() - text.get_width() - 10, 8 + i * 18))


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
        f"Aggression {player.aggression:.2f}   Strength {player.fighting_strength():.1f}"
        f"   Speed {player.speed:.2f}",
        f"Kills: {player.kills}   Weapon: {weapon}",
        f"Food {player.inventory['food']}   Water {player.inventory['water']}",
        f"Alliance: {alliance}",
    ]
    if player.injury_timer > 0:
        lines.append(f"Injured ({player.injury_timer // FPS} s)")
    if player.nemesis is not None and player.nemesis.alive:
        lines.append(f"Seeking revenge on {player.nemesis.name}")
    return lines


def draw_inspector(screen, font, player):
    """A panel (top left) about the selected tribute, with its needs as bars."""
    lines = inspector_lines(player)
    width = 330
    height = 16 + len(lines) * 18 + 3 * 14 + 8
    panel = pygame.Rect(10, 10, width, height)
    pygame.draw.rect(screen, PANEL_COLOR, panel, border_radius=6)
    pygame.draw.rect(screen, PANEL_BORDER, panel, 1, border_radius=6)
    y = panel.y + 8
    for i, line in enumerate(lines):
        screen.blit(font.render(line, True, PANEL_BORDER if i == 0 else HUD_TEXT_COLOR), (panel.x + 10, y))
        y += 18
    for name, value in player.needs.items():
        screen.blit(font.render(name, True, HUD_TEXT_COLOR), (panel.x + 10, y))
        pygame.draw.rect(screen, (50, 50, 50), (panel.x + 70, y + 3, 240, 8))
        pygame.draw.rect(screen, NEED_WARNING_COLORS[name], (panel.x + 70, y + 3, int(240 * value / 100), 8))
        y += 14


def draw(screen, fonts, sim, camera, debug, speed, paused, selected=None):
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
        player.draw(screen, camera, name_font, debug)
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
    draw_hud(screen, font, speed, paused, camera, sim)
    draw_minimap(screen, sim, camera)
    if selected is not None:
        draw_inspector(screen, font, selected)
    pygame.display.flip()


def tribute_at(sim, camera, screen, position):
    """The living tribute under a screen position (within a few pixels), or None."""
    world_x, world_y = camera.screen_to_world(*position, screen)
    closest = min(sim.players, default=None,
                  key=lambda player: distance(player.x, player.y, world_x, world_y))
    if closest is not None and distance(closest.x, closest.y, world_x, world_y) * camera.zoom <= 15:
        return closest
    return None


# --- Running the Games -----------------------------------------------------

def play(screen, clock, names, seed=None):
    """Run one Games from the countdown until shortly after the winner is
    known. Returns the finished Simulation (for the debrief), or None if the
    window was closed."""
    fonts = (
        pygame.font.Font(None, 20),   # HUD, legend and event feed (None = pygame's built-in font)
        pygame.font.Font(None, 140),  # countdown
        pygame.font.Font(None, 16),   # names above heads
        pygame.font.Font(None, 80),   # winner banner
    )
    events.reset()
    sim = Simulation(names, seed)
    camera = Camera(sim.arena.center_x, sim.arena.center_y, CAMERA_OPENING_ZOOM)
    debug = False
    paused = False
    speed_index = SPEED_LEVELS.index(1)  # start at normal speed
    step_budget = 0.0  # simulation steps owed; lets speeds below 1 skip frames
    frames_after_end = 0  # frames the winner banner has been shown
    selected = None       # the tribute shown in the inspector panel
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
        if not paused and not sim.game_over:  # once there is a winner, the arena freezes
            # E.g. at speed 4 the budget grows by 4 each frame, so step() runs
            # 4 times; at 0.5 it grows by 0.5, so step() runs every other frame.
            step_budget += speed
            while step_budget >= 1:
                sim.step()
                step_budget -= 1

        camera.update(sim, screen)
        draw(screen, fonts, sim, camera, debug, speed, paused, selected)
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

    names = None  # the first start screen uses the default names
    seed = None   # None = a new random seed
    while True:
        if seed is None:
            names = run_start_screen(screen, clock, names)
            if names is None:  # window closed on the start screen
                break
        sim = play(screen, clock, names, seed)
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
