import math
import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BACKGROUND_COLOR, NUM_PLAYERS, START_CIRCLE_RADIUS, LEGEND_TEXT_COLOR,
    CHASE_LINE_COLOR,
)
from player import Player
from arena import Arena
import ai
import alliances
import combat


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
    game_over = False
    print("Press D to toggle the debug view (vision circles, state colors, alliance lines).")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                debug = not debug

        # Update pass: every player acts before anything is drawn, so
        # the frame that gets drawn shows one consistent world state.
        alliances.share_supplies(players)  # allies hand over food/water first
        for player in players:
            ai.decide(player, arena, players)  # choose state and target
            player.move()
            player.use_supplies()     # before needs drop, so a carried item can save them
            player.update_needs()

        # Hunters that have reached their prey fight
        combat.handle_fights(players, arena)
        arena.update_flashes()

        # Remove players who died this frame. `survivors` is a new list
        # containing only the living players; it replaces the old list.
        survivors = [player for player in players if player.alive]
        for player in players:
            if not player.alive:
                if player.cause_of_death == "combat":
                    how = f"was eliminated by Player {player.killer_id}"
                else:
                    how = f"died of {player.cause_of_death}"
                print(f"Player {player.id} {how}. {len(survivors)} remaining.")
        players = survivors

        # Remove dead members, replace dead leaders, handle betrayals
        alliances.update_alliances(players)

        if not game_over and len(players) <= 1:
            game_over = True
            if players:
                winner = players[0]
                print(f"Player {winner.id} is the last one standing, with {winner.kills} kill(s).")
            else:
                print("No survivors.")

        # Living players pick up any loot they are touching
        arena.handle_pickups(players)

        # Draw pass
        screen.fill(BACKGROUND_COLOR)
        if debug:
            for player in players:
                player.draw_vision(screen)
                # Line from each alliance member to its leader
                if player.alliance is not None and player.alliance.leader is not player:
                    leader = player.alliance.leader
                    pygame.draw.line(screen, player.alliance.color,
                                     (int(player.x), int(player.y)),
                                     (int(leader.x), int(leader.y)))
        arena.draw(screen)      # loot and fight markers before players, so players are on top
        # Faint line from each hunter to the player it is chasing
        for player in players:
            if player.state == ai.HUNTING and player.prey is not None and player.prey.alive:
                pygame.draw.line(screen, CHASE_LINE_COLOR,
                                 (int(player.x), int(player.y)),
                                 (int(player.prey.x), int(player.prey.y)))
        for player in players:
            player.draw(screen, debug)
        if debug:
            draw_legend(screen, font)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
