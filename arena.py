import math
import random

import pygame
from config import (
    WORLD_WIDTH, WORLD_HEIGHT, PLAYER_RADIUS, FPS, NUM_PLAYERS, START_CIRCLE_RADIUS,
    ITEM_DROP_SCATTER, FIGHT_FLASH_SECONDS, FIGHT_FLASH_COLOR, FIGHT_FLASH_RADIUS, FIGHT_RING_COLOR,
    LOOT_COUNTS, LOOT_CENTER_FRACTION, LOOT_CENTER_SPREAD, LOOT_SIZE, LOOT_COLORS,
    CORNUCOPIA_SIZE, CORNUCOPIA_COLOR, CORNUCOPIA_OUTLINE_COLOR, PLATE_RADIUS, PLATE_COLOR,
    TERRAIN_COLORS, TERRAIN_WEIGHTS, TERRAIN_ZONES, TERRAIN_CELL, TERRAIN_CLEAR_RADIUS,
    OUTSIDE_COLOR, BORDER_COLOR, MINIMAP_WIDTH,
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
    """Owns everything in the arena that is not a player: the terrain, the
    cornucopia and launch plates, the loot, and fights in progress."""

    def __init__(self):
        self.center_x = WORLD_WIDTH / 2
        self.center_y = WORLD_HEIGHT / 2
        self.plates = self.launch_plate_positions()
        self.horn, self.mouth, self.mouth_radius = self.cornucopia_shape()
        self.loot = []
        self.fights = []            # fights in progress (combat.Fight objects)
        self.flashes = []           # short markers where fights ended, each [x, y, frames_left]
        self.spawn_loot()
        self.background = self.paint_background()
        # A small copy of the terrain for the minimap, made once
        minimap_height = int(WORLD_HEIGHT * MINIMAP_WIDTH / WORLD_WIDTH)
        self.minimap = pygame.transform.smoothscale(self.background, (MINIMAP_WIDTH, minimap_height))

    # --- The start ---------------------------------------------------------

    def launch_plate_positions(self):
        """One launch plate per player, evenly spaced on a circle around the cornucopia."""
        plates = []
        for i in range(NUM_PLAYERS):
            angle = (2 * math.pi / NUM_PLAYERS) * i
            plates.append((self.center_x + START_CIRCLE_RADIUS * math.cos(angle),
                           self.center_y + START_CIRCLE_RADIUS * math.sin(angle)))
        return plates

    def cornucopia_shape(self):
        """The golden horn: its outline (a list of world points), the center
        of its open mouth, and the mouth's radius.

        The horn follows a curved line (its "spine") from the wide mouth to
        the narrow tip. At each step along the spine we step out sideways on
        both sides by the horn's width at that point. The left-side points
        followed by the right-side points (in reverse) outline the horn."""
        s = CORNUCOPIA_SIZE
        mouth = (self.center_x - 0.15 * s, self.center_y + 0.2 * s)
        bend = (self.center_x + 0.6 * s, self.center_y + 0.25 * s)   # pulls the spine into a curve
        tip = (self.center_x + 0.65 * s, self.center_y - 0.45 * s)
        left, right = [], []
        steps = 12
        for i in range(steps + 1):
            t = i / steps  # 0 at the mouth, 1 at the tip
            # A point on the curve from mouth to tip (a "Bezier curve")
            x = (1 - t) ** 2 * mouth[0] + 2 * (1 - t) * t * bend[0] + t ** 2 * tip[0]
            y = (1 - t) ** 2 * mouth[1] + 2 * (1 - t) * t * bend[1] + t ** 2 * tip[1]
            # The direction the curve is heading at that point
            dx = 2 * (1 - t) * (bend[0] - mouth[0]) + 2 * t * (tip[0] - bend[0])
            dy = 2 * (1 - t) * (bend[1] - mouth[1]) + 2 * t * (tip[1] - bend[1])
            length = math.hypot(dx, dy) or 1  # `or 1` avoids dividing by zero
            # Sideways (perpendicular) to that direction, as long as the width here
            width = (0.32 * (1 - t) + 0.03 * t) * s
            side_x, side_y = -dy / length * width, dx / length * width
            left.append((x + side_x, y + side_y))
            right.append((x - side_x, y - side_y))
        return left + right[::-1], mouth, 0.26 * s  # [::-1] is the list reversed

    # --- Loot ----------------------------------------------------------------

    def spawn_loot(self):
        """Pile part of each item type at the cornucopia's mouth (most of the
        weapons) and spread the rest evenly over the whole arena."""
        scattered_kinds = []
        for kind, count in LOOT_COUNTS.items():
            center_count = round(count * LOOT_CENTER_FRACTION[kind])
            for _ in range(center_count):
                x, y = self.random_point_near_cornucopia()
                self.loot.append(LootItem(kind, x, y))
            # The rest of this kind is placed below, after all kinds are known
            scattered_kinds += [kind] * (count - center_count)

        # Mix the kinds so no part of the arena gets only one type
        random.shuffle(scattered_kinds)
        points = self.evenly_spread_points(len(scattered_kinds))
        # zip() pairs the lists up: first kind with first point, and so on
        for kind, (x, y) in zip(scattered_kinds, points):
            self.loot.append(LootItem(kind, x, y))

    def random_point_near_cornucopia(self):
        """A random point that is very likely close to the horn's mouth.

        random.gauss(mean, spread) returns numbers that cluster around
        `mean` — most land within `spread` of it, few land far away."""
        mouth_x, mouth_y = self.mouth
        return (random.gauss(mouth_x, LOOT_CENTER_SPREAD),
                random.gauss(mouth_y, LOOT_CENTER_SPREAD))

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
        cols = math.ceil(math.sqrt(count * WORLD_WIDTH / WORLD_HEIGHT))
        rows = math.ceil(count / cols)
        cell_w = WORLD_WIDTH / cols
        cell_h = WORLD_HEIGHT / rows

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
        x = random.uniform(margin, WORLD_WIDTH - margin)
        y = random.uniform(margin, WORLD_HEIGHT - margin)
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
        x = max(LOOT_SIZE, min(x, WORLD_WIDTH - LOOT_SIZE))
        y = max(LOOT_SIZE, min(y, WORLD_HEIGHT - LOOT_SIZE))
        self.loot.append(LootItem(kind, x, y, dropped_by))

    # --- Fight markers -------------------------------------------------------

    def add_flash(self, x, y):
        """Show a short-lived ring where a fight was decided."""
        self.flashes.append([x, y, int(FIGHT_FLASH_SECONDS * FPS)])

    def update_flashes(self):
        """Count every fight marker down by one frame and remove expired ones."""
        for flash in self.flashes:
            flash[2] -= 1
        self.flashes = [flash for flash in self.flashes if flash[2] > 0]

    # --- Terrain and drawing ------------------------------------------------

    def paint_background(self):
        """Paint the terrain once onto one large image: a few big colored areas
        (meadow, forest, rock, sand, marsh) and a meadow clearing around the
        cornucopia. Each frame the camera shows part of this image.

        How the areas are made: TERRAIN_ZONES "zone centers" are scattered over
        the arena, each with a terrain type, and every spot takes the type of
        its nearest zone center. To keep this fast it is worked out on a coarse
        grid (one block per TERRAIN_CELL world pixels) and then scaled up with
        smoothing, which also softens the borders between areas."""
        kinds = random.choices(list(TERRAIN_WEIGHTS), weights=list(TERRAIN_WEIGHTS.values()),
                               k=TERRAIN_ZONES)  # k = how many to pick
        zones = [(random.uniform(0, WORLD_WIDTH), random.uniform(0, WORLD_HEIGHT), kind)
                 for kind in kinds]

        cols = WORLD_WIDTH // TERRAIN_CELL
        rows = WORLD_HEIGHT // TERRAIN_CELL
        small = pygame.Surface((cols, rows), 0, 32)  # 32 bits per pixel, needed for smoothscale
        for col in range(cols):
            for row in range(rows):
                x = (col + 0.5) * TERRAIN_CELL
                y = (row + 0.5) * TERRAIN_CELL
                if distance(x, y, self.center_x, self.center_y) <= TERRAIN_CLEAR_RADIUS:
                    kind = "meadow"
                else:
                    closest = min(zones, key=lambda zone: distance(x, y, zone[0], zone[1]))
                    kind = closest[2]
                small.set_at((col, row), TERRAIN_COLORS[kind])

        surface = pygame.transform.smoothscale(small, (WORLD_WIDTH, WORLD_HEIGHT))
        pygame.draw.rect(surface, BORDER_COLOR, surface.get_rect(), 6)  # 6 = line width
        return surface

    def draw_background(self, screen, camera):
        """Show the part of the background image that is in view, scaled to the zoom."""
        screen.fill(OUTSIDE_COLOR)
        width, height = screen.get_size()
        left, top = camera.screen_to_world(0, 0, screen)
        right, bottom = camera.screen_to_world(width, height, screen)
        view = pygame.Rect(int(left), int(top), int(right - left) + 2, int(bottom - top) + 2)
        view = view.clip(self.background.get_rect())  # only the part inside the arena
        if view.width <= 0 or view.height <= 0:
            return
        part = self.background.subsurface(view)  # a window into the big image, no copying
        scaled_size = (max(1, int(view.width * camera.zoom)), max(1, int(view.height * camera.zoom)))
        screen.blit(pygame.transform.scale(part, scaled_size),
                    camera.world_to_screen(view.x, view.y, screen))

    def draw(self, screen, camera):
        self.draw_background(screen, camera)

        for x, y in self.plates:
            pygame.draw.circle(screen, PLATE_COLOR, camera.world_to_screen(x, y, screen),
                               camera.size(PLATE_RADIUS, 2))

        horn_points = [camera.world_to_screen(x, y, screen) for x, y in self.horn]
        pygame.draw.polygon(screen, CORNUCOPIA_COLOR, horn_points)
        pygame.draw.polygon(screen, CORNUCOPIA_OUTLINE_COLOR, horn_points, 2)
        pygame.draw.circle(screen, CORNUCOPIA_OUTLINE_COLOR,  # the dark opening
                           camera.world_to_screen(*self.mouth, screen), camera.size(self.mouth_radius, 2))

        size = camera.size(LOOT_SIZE, 2)
        for item in self.loot:
            screen_x, screen_y = camera.world_to_screen(item.x, item.y, screen)
            pygame.draw.rect(screen, LOOT_COLORS[item.kind],
                             (screen_x - size // 2, screen_y - size // 2, size, size))

        for fight in self.fights:
            # A pulsing ring around a fight in progress (sin swings between -1 and 1)
            pulse = 3 * math.sin(fight.frames_left * 0.3)
            pygame.draw.circle(screen, FIGHT_RING_COLOR, camera.world_to_screen(fight.x, fight.y, screen),
                               camera.size(FIGHT_FLASH_RADIUS + pulse, 6), 2)

        for x, y, _ in self.flashes:  # _ = the frames_left value, not needed here
            pygame.draw.circle(screen, FIGHT_FLASH_COLOR, camera.world_to_screen(x, y, screen),
                               camera.size(FIGHT_FLASH_RADIUS, 6), 2)
