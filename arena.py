import math
import random

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_RADIUS,
    LOOT_COUNTS, LOOT_SPREAD, LOOT_SIZE, LOOT_COLORS,
)


class LootItem:
    """A single item lying on the ground."""

    def __init__(self, kind, x, y):
        self.kind = kind  # "food", "water" or "weapon"
        self.x = x
        self.y = y


class Arena:
    """Owns everything in the arena that is not a player — for now, loot."""

    def __init__(self):
        self.center_x = SCREEN_WIDTH / 2
        self.center_y = SCREEN_HEIGHT / 2
        self.loot = []
        self.spawn_loot()

    def spawn_loot(self):
        for kind, count in LOOT_COUNTS.items():
            for _ in range(count):
                x, y = self.random_point_near_center()
                self.loot.append(LootItem(kind, x, y))

    def random_point_near_center(self):
        """Pick a random point where points near the center are more
        likely than points near the edges.

        random.gauss(mean, spread) returns numbers that cluster around
        `mean` — most land within `spread` of it, few land far away.
        If a point falls outside the arena we simply try again."""
        margin = LOOT_SIZE
        while True:
            x = random.gauss(self.center_x, LOOT_SPREAD)
            y = random.gauss(self.center_y, LOOT_SPREAD)
            if margin <= x <= SCREEN_WIDTH - margin and margin <= y <= SCREEN_HEIGHT - margin:
                return x, y

    def handle_pickups(self, players):
        """Give each item to the first player touching it, and remove
        picked-up items from the ground."""
        pickup_distance = PLAYER_RADIUS + LOOT_SIZE / 2
        remaining = []
        for item in self.loot:
            picked_up = False
            for player in players:
                # math.hypot gives the straight-line distance between two points
                if math.hypot(player.x - item.x, player.y - item.y) <= pickup_distance:
                    player.pick_up(item.kind)
                    picked_up = True
                    break  # only one player can take this item
            if not picked_up:
                remaining.append(item)
        self.loot = remaining

    def draw(self, screen):
        half = LOOT_SIZE // 2
        for item in self.loot:
            rect = pygame.Rect(int(item.x) - half, int(item.y) - half, LOOT_SIZE, LOOT_SIZE)
            pygame.draw.rect(screen, LOOT_COLORS[item.kind], rect)
