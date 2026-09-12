import math
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BACKGROUND_COLOR, NUM_PLAYERS, START_CIRCLE_RADIUS
)
from player import Player


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


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hunger Games Simulation")
    clock = pygame.time.Clock()

    players = create_starting_players()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update pass: every player moves before anything is drawn, so
        # the frame that gets drawn shows one consistent world state.
        for player in players:
            player.move()

        # Draw pass
        screen.fill(BACKGROUND_COLOR)
        for player in players:
            player.draw(screen)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()