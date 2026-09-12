import math
import random

import pygame
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_RADIUS, FPS,
    ITEM_DROP_SCATTER, FIGHT_FLASH_SECONDS, FIGHT_FLASH_COLOR, FIGHT_FLASH_RADIUS,
    LOOT_COUNTS, LOOT_CENTER_FRACTION, LOOT_CENTER_SPREAD, LOOT_SIZE, LOOT_COLORS,
)
from utils import distance


class LootItem:
    """A single item lying on the ground."""

    def __init__(self, kind, x, y, dropped_by=None):
        self.kind = kind  # "food", "water" or "weapon"
        # The player who dropped this item in a fight (None for spawned
        # loot). That player will not pick it back up.
        self.dropped_by = dropped_by
        self.x = x
        self.y = y
        # Set to True when picked up. Players who remember this item only
        # find out it is gone when they can see its spot again.
        self.taken = False


class Arena:
    """Owns everything in the arena that is not a player — for now, loot."""

    def __init__(self):
        self.center_x = SCREEN_WIDTH / 2
        self.center_y = SCREEN_HEIGHT / 2
        self.loot = []
        self.flashes = []  # fight markers, each [x, y, frames_left]
        self.spawn_loot()

    def spawn_loot(self):
        """Put part of each item type in a tight cluster at the center and
        spread the rest evenly over the whole arena."""
        scattered_kinds = []
        for kind, count in LOOT_COUNTS.items():
            center_count = round(count * LOOT_CENTER_FRACTION)
            for _ in range(center_count):
                x, y = self.random_point_near_center()
                self.loot.append(LootItem(kind, x, y))
            # The rest of this kind is placed below, after all kinds are known
            scattered_kinds += [kind] * (count - center_count)

        # Mix the kinds so no part of the arena gets only one type
        random.shuffle(scattered_kinds)
        points = self.evenly_spread_points(len(scattered_kinds))
        # zip() pairs the lists up: first kind with first point, and so on
        for kind, (x, y) in zip(scattered_kinds, points):
            self.loot.append(LootItem(kind, x, y))

    def random_point_near_center(self):
        """A random point that is very likely close to the center.

        random.gauss(mean, spread) returns numbers that cluster around
        `mean` — most land within `spread` of it, few land far away.
        If a point falls outside the arena we simply try again."""
        margin = LOOT_SIZE
        while True:
            x = random.gauss(self.center_x, LOOT_CENTER_SPREAD)
            y = random.gauss(self.center_y, LOOT_CENTER_SPREAD)
            if margin <= x <= SCREEN_WIDTH - margin and margin <= y <= SCREEN_HEIGHT - margin:
                return x, y

    def evenly_spread_points(self, count):
        """`count` points spread evenly over the arena.

        Purely random points can clump together by chance. Instead, the
        arena is divided into a grid of cells, `count` different cells are
        picked at random, and each point goes somewhere inside its cell.
        That guarantees no two points share a cell."""
        if count == 0:
            return []
        # Choose columns/rows so cells are roughly square and there are at
        # least `count` of them.
        cols = math.ceil(math.sqrt(count * SCREEN_WIDTH / SCREEN_HEIGHT))
        rows = math.ceil(count / cols)
        cell_w = SCREEN_WIDTH / cols
        cell_h = SCREEN_HEIGHT / rows

        all_cells = [(col, row) for col in range(cols) for row in range(rows)]
        chosen_cells = random.sample(all_cells, count)  # `count` distinct cells

        margin = LOOT_SIZE
        points = []
        for col, row in chosen_cells:
            x = random.uniform(col * cell_w + margin, (col + 1) * cell_w - margin)
            y = random.uniform(row * cell_h + margin, (row + 1) * cell_h - margin)
            points.append((x, y))
        return points

    def random_point(self, margin):
        """A completely random point in the arena, at least `margin` from the edges."""
        x = random.uniform(margin, SCREEN_WIDTH - margin)
        y = random.uniform(margin, SCREEN_HEIGHT - margin)
        return x, y

    def handle_pickups(self, players):
        """Give each item to the first player touching it who can still
        carry it, and remove picked-up items from the ground."""
        pickup_distance = PLAYER_RADIUS + LOOT_SIZE / 2
        remaining = []
        for item in self.loot:
            for player in players:
                if player.can_carry(item.kind) and player is not item.dropped_by and \
                        distance(player.x, player.y, item.x, item.y) <= pickup_distance:
                    player.pick_up(item.kind)
                    item.taken = True
                    break  # only one player can take this item
            if not item.taken:
                remaining.append(item)
        self.loot = remaining

    def drop_item(self, kind, x, y, dropped_by):
        """Put an item on the ground a short random distance from (x, y)."""
        x += random.uniform(-ITEM_DROP_SCATTER, ITEM_DROP_SCATTER)
        y += random.uniform(-ITEM_DROP_SCATTER, ITEM_DROP_SCATTER)
        x = max(LOOT_SIZE, min(x, SCREEN_WIDTH - LOOT_SIZE))
        y = max(LOOT_SIZE, min(y, SCREEN_HEIGHT - LOOT_SIZE))
        self.loot.append(LootItem(kind, x, y, dropped_by))

    def add_flash(self, x, y):
        """Show a short-lived ring where a fight happened."""
        self.flashes.append([x, y, int(FIGHT_FLASH_SECONDS * FPS)])

    def update_flashes(self):
        """Count every fight marker down by one frame and remove expired ones."""
        for flash in self.flashes:
            flash[2] -= 1
        self.flashes = [flash for flash in self.flashes if flash[2] > 0]

    def draw(self, screen):
        half = LOOT_SIZE // 2
        for item in self.loot:
            rect = pygame.Rect(int(item.x) - half, int(item.y) - half, LOOT_SIZE, LOOT_SIZE)
            pygame.draw.rect(screen, LOOT_COLORS[item.kind], rect)
        for x, y, _ in self.flashes:  # _ = the frames_left value, not needed here
            pygame.draw.circle(screen, FIGHT_FLASH_COLOR, (int(x), int(y)), FIGHT_FLASH_RADIUS, 2)
