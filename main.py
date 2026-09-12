import math
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BACKGROUND_COLOR, NUM_PLAYERS, START_CIRCLE_RADIUS, LEGEND_TEXT_COLOR,
)
from player import Player
from arena import Arena
import ai


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


def draw_legend(screen, font):
    """Debug view: list each state with its dot color in the top-left corner."""
    y = 8
    for state, color in ai.STATE_COLORS.items():
        pygame.draw.circle(screen, color, (14, y + 7), 5)
        text = font.render(state, True, LEGEND_TEXT_COLOR)
        screen.blit(text, (26, y))  # blit = copy the rendered text onto the screen
        y += 18


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hunger Games Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)  # None = pygame's built-in font

    arena = Arena()
    players = create_starting_players()
    for player in players:
        ai.choose_opening_state(player, arena)

    debug = False
    print("Press D to toggle the debug view (vision circles and state colors).")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                debug = not debug

        # Update pass: every player acts before anything is drawn, so
        # the frame that gets drawn shows one consistent world state.
        for player in players:
            ai.decide(player, arena)  # choose state and target
            player.move()
            player.use_supplies()     # before needs drop, so a carried item can save them
            player.update_needs()

        # Remove players who died this frame. `survivors` is a new list
        # containing only the living players; it replaces the old list.
        survivors = [player for player in players if player.alive]
        for player in players:
            if not player.alive:
                print(f"Player {player.id} died of {player.cause_of_death}. "
                      f"{len(survivors)} remaining.")
        players = survivors

        # Living players pick up any loot they are touching
        arena.handle_pickups(players)

        # Draw pass
        screen.fill(BACKGROUND_COLOR)
        if debug:
            for player in players:
                player.draw_vision(screen)
        arena.draw(screen)      # loot before players, so players are drawn on top
        for player in players:
            player.draw(screen, debug)
        if debug:
            draw_legend(screen, font)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
