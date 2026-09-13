import math
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BACKGROUND_COLOR, NUM_PLAYERS, START_CIRCLE_RADIUS, LEGEND_TEXT_COLOR,
    CHASE_LINE_COLOR, SHOWDOWN_PLAYERS, SPEED_LEVELS, HUD_TEXT_COLOR,
)
from player import Player
from arena import Arena
import ai
import alliances
import combat
import events


def create_starting_players():
    """Place NUM_PLAYERS players evenly spaced around a circle
    at the center of the arena."""
    center_x = SCREEN_WIDTH // 2
    center_y = SCREEN_HEIGHT // 2

    players = []
    for i in range(NUM_PLAYERS):
        angle = (2 * math.pi / NUM_PLAYERS) * i
        x = center_x + START_CIRCLE_RADIUS * math.cos(angle)
        y = center_y + START_CIRCLE_RADIUS * math.sin(angle)
        players.append(Player(player_id=i, x=x, y=y))
    return players


class Simulation:
    """Everything that changes while the game runs: the arena, the players
    and a few flags. step() moves the whole world forward by one tick, so
    the main loop can run it several times per frame (faster) or skip it
    (paused)."""

    def __init__(self):
        self.arena = Arena()
        self.players = create_starting_players()
        for player in self.players:
            ai.choose_opening_state(player, self.arena)
        self.game_over = False
        self.showdown_announced = False

        print("Players:")
        for player in self.players:
            print(f"  Player {player.id:>2}: {player.temperament}, {player.roaming} "
                  f"(aggression {player.aggression:.2f}, strength {player.strength:.1f}, "
                  f"speed {player.speed:.1f})")

    def step(self):
        players = self.players  # shorter name for use below

        # Every player acts before anything is drawn, so the drawn frame
        # shows one consistent world state.
        alliances.share_supplies(players)  # allies hand over food/water first
        for player in players:
            ai.decide(player, self.arena, players)  # choose state and target
            player.move()
            player.use_supplies()     # before needs drop, so a carried item can save them
            player.update_needs()

        # Hunters that have reached their prey fight
        combat.handle_fights(players, self.arena)
        self.arena.update_flashes()
        events.update()

        # Remove players who died this step
        survivors = [player for player in players if player.alive]
        for player in players:
            if not player.alive:
                if player.cause_of_death == "combat":
                    how = f"was eliminated by Player {player.killer_id}"
                else:
                    how = f"died of {player.cause_of_death}"
                events.log(f"Player {player.id} {how}. {len(survivors)} remaining.")
        self.players = survivors

        # Remove dead members, replace dead leaders, handle betrayals
        alliances.update_alliances(self.players)

        if not self.showdown_announced and 1 < len(self.players) <= SHOWDOWN_PLAYERS:
            self.showdown_announced = True
            events.log(f"Showdown! {len(self.players)} players left - they hunt each other to the death.")

        if not self.game_over and len(self.players) <= 1:
            self.game_over = True
            if self.players:
                winner = self.players[0]
                events.log(f"Player {winner.id} ({winner.temperament}) is the last one standing, "
                           f"with {winner.kills} kill(s).")
            else:
                events.log("No survivors.")

        # Living players pick up any loot they are touching
        self.arena.handle_pickups(self.players)


def draw_legend(screen, font):
    """Debug view: list each state with its dot color in the top-left corner."""
    y = 8
    for state, color in ai.STATE_COLORS.items():
        pygame.draw.circle(screen, color, (14, y + 7), 5)
        text = font.render(state, True, LEGEND_TEXT_COLOR)
        screen.blit(text, (26, y))  # blit = copy the rendered text onto the screen
        y += 18


def draw_hud(screen, font, speed, paused):
    """Speed (or PAUSED) and the key hints in the top-right corner."""
    status = "PAUSED" if paused else f"Speed {speed:g}x"  # :g drops needless decimals (2.0 -> 2)
    lines = [status, "Space: pause   Up/Down: speed   D: debug"]
    for i, line in enumerate(lines):
        text = font.render(line, True, HUD_TEXT_COLOR)
        # Right-align: start the text its own width away from the right edge
        screen.blit(text, (SCREEN_WIDTH - text.get_width() - 10, 8 + i * 18))


def draw(screen, font, sim, debug, speed, paused):
    screen.fill(BACKGROUND_COLOR)
    if debug:
        for player in sim.players:
            player.draw_vision(screen)
            # Line from each alliance member to its leader
            if player.alliance is not None and player.alliance.leader is not player:
                leader = player.alliance.leader
                pygame.draw.line(screen, player.alliance.color,
                                 (int(player.x), int(player.y)),
                                 (int(leader.x), int(leader.y)))
    sim.arena.draw(screen)  # loot and fight markers before players, so players are on top
    # Faint line from each hunter to the player it is chasing
    for player in sim.players:
        if player.state == ai.HUNTING and player.prey is not None and player.prey.alive:
            pygame.draw.line(screen, CHASE_LINE_COLOR,
                             (int(player.x), int(player.y)),
                             (int(player.prey.x), int(player.prey.y)))
    for player in sim.players:
        player.draw(screen, debug)
    if debug:
        draw_legend(screen, font)
    events.draw(screen, font)
    draw_hud(screen, font, speed, paused)
    pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hunger Games Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)  # None = pygame's built-in font

    sim = Simulation()
    debug = False
    paused = False
    speed_index = SPEED_LEVELS.index(1)  # start at normal speed
    step_budget = 0.0  # simulation steps owed; lets speeds below 1 skip frames

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_d:
                    debug = not debug
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_UP:
                    speed_index = min(speed_index + 1, len(SPEED_LEVELS) - 1)
                elif event.key == pygame.K_DOWN:
                    speed_index = max(speed_index - 1, 0)

        speed = SPEED_LEVELS[speed_index]
        if not paused:
            # E.g. at speed 4 the budget grows by 4 each frame, so step() runs
            # 4 times; at 0.5 it grows by 0.5, so step() runs every other frame.
            step_budget += speed
            while step_budget >= 1:
                sim.step()
                step_budget -= 1

        draw(screen, font, sim, debug, speed, paused)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
