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
)
from player import Player
from arena import Arena
from camera import Camera
from start_screen import run_start_screen
from debrief import run_debrief
import ai
import alliances
import combat
import events


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

    def __init__(self, names):
        self.arena = Arena()
        self.players = create_starting_players(self.arena, names)
        self.all_players = list(self.players)  # everyone, including the fallen (for the debrief)
        for player in self.players:
            ai.set_state(player, ai.WAITING)
        self.countdown_frames = COUNTDOWN_SECONDS * FPS  # players wait on their plates
        self.frames_since_start = 0
        self.opening_over = False   # True once the rush and flight from the cornucopia are done
        self.bloodbath_deaths = 0
        self.quiet_frames = 0       # frames in a row with no fight going on
        self.finale_announced = False
        self.game_over = False

        print("Tributes:")
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
                events.log("The Games have begun!")
            return
        self.frames_since_start += 1

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

        # A long quiet spell (not during the opening or the finale): the
        # Gamemakers point the aggressive players at the nearest tributes
        if self.opening_over and len(players) > SHOWDOWN_PLAYERS and \
                self.arena.frames_since_fight >= LULL_SECONDS * FPS:
            self.arena.frames_since_fight = 0
            told = ai.reveal_positions(players)
            if told:
                events.log(f"The arena has gone quiet. The Gamemakers reveal nearby "
                           f"tributes to {told} hunter(s).")
        events.update()

        # Remove players who died this step. Everyone who falls in the same
        # step shares the same place in the standings.
        survivors = [player for player in players if player.alive]
        for player in players:
            if not player.alive:
                player.placement = len(survivors) + 1
                player.death_frame = self.frames_since_start
                if player.cause_of_death == "combat":
                    how = f"was eliminated by {player.killer_name}"
                else:
                    how = f"died of {player.cause_of_death}"
                events.log(f"{player.name} {how}. {len(survivors)} remaining.")
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
            self.bloodbath_deaths = NUM_PLAYERS - len(self.players)
            events.log(f"The bloodbath is over: {self.bloodbath_deaths} tribute(s) fell.")

        if not self.finale_announced and 1 < len(self.players) <= SHOWDOWN_PLAYERS:
            self.finale_announced = True
            events.log(f"The finale! {len(self.players)} tributes remain and are drawn "
                       f"to the cornucopia to fight to the death.")

        if not self.game_over and len(self.players) <= 1:
            self.game_over = True
            if self.players:
                winner = self.players[0]
                winner.placement = 1
                events.log(f"{winner.name} ({winner.temperament}) is the last one standing, "
                           f"with {winner.kills} kill(s).")
            else:
                events.log("No survivors.")

        # Living players pick up any loot they are touching
        self.arena.handle_pickups(self.players)


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


def draw_hud(screen, font, speed, paused, camera):
    """Speed, camera mode and key hints in the top-right corner."""
    status = "PAUSED" if paused else f"Speed {speed:g}x"  # :g drops needless decimals (2.0 -> 2)
    camera_mode = "auto" if camera.auto else "manual"
    lines = [
        f"{status}   Camera: {camera_mode}",
        "Space: pause   Up/Down: speed   Tab: debug",
        "Wheel / drag / WASD: camera   F: follow   C: whole map",
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

    pygame.draw.circle(screen, CORNUCOPIA_COLOR, to_map(sim.arena.center_x, sim.arena.center_y), 3)
    for player in sim.players:
        color = player.alliance.color if player.alliance is not None else PLAYER_COLOR
        pygame.draw.circle(screen, color, to_map(player.x, player.y), 2)

    left, top = camera.screen_to_world(0, 0, screen)
    right, bottom = camera.screen_to_world(width, height, screen)
    view = pygame.Rect(to_map(left, top), (int((right - left) * scale), int((bottom - top) * scale)))
    pygame.draw.rect(screen, MINIMAP_BORDER, view.clip(map_rect), 1)
    pygame.draw.rect(screen, MINIMAP_BORDER, map_rect, 1)


def draw(screen, fonts, sim, camera, debug, speed, paused):
    font, big_font, name_font, banner_font = fonts
    sim.arena.draw(screen, camera)  # terrain, cornucopia, plates, loot, fight markers

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

    draw_countdown(screen, big_font, sim)
    if sim.game_over:
        draw_big_text(screen, banner_font, f"{sim.players[0].name} wins!" if sim.players else "No victor")
    if debug:
        draw_legend(screen, font)
    events.draw(screen, font)
    draw_hud(screen, font, speed, paused, camera)
    draw_minimap(screen, sim, camera)
    pygame.display.flip()


# --- Running the Games -----------------------------------------------------

def play(screen, clock, names):
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
    sim = Simulation(names)
    camera = Camera(sim.arena.center_x, sim.arena.center_y, CAMERA_OPENING_ZOOM)
    debug = False
    paused = False
    speed_index = SPEED_LEVELS.index(1)  # start at normal speed
    step_budget = 0.0  # simulation steps owed; lets speeds below 1 skip frames
    frames_after_end = 0  # frames the winner banner has been shown

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
            else:
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
        draw(screen, fonts, sim, camera, debug, speed, paused)
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
    while True:
        names = run_start_screen(screen, clock, names)
        if names is None:  # window closed on the start screen
            break
        sim = play(screen, clock, names)
        if sim is None:    # window closed during the Games
            break
        if run_debrief(screen, clock, sim) == "quit":
            break
        # "again": back to the start screen, keeping the names

    pygame.quit()


if __name__ == "__main__":
    main()
