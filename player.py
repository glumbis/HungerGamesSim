import math
import random

import pygame
from config import (
    PLAYER_RADIUS, PLAYER_COLOR,
    PLAYER_MIN_SPEED, PLAYER_MAX_SPEED, WANDER_TURN_RATE,
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    NEED_MAX, NEED_WARNING_THRESHOLD, NEED_SECONDS_TO_EMPTY,
    NEED_RATE_VARIATION, NEED_WARNING_COLORS,
    WARNING_DOT_RADIUS, WARNING_DOT_SPACING, WARNING_DOT_OFFSET_Y,
)


class Player:
    def __init__(self, player_id, x, y):
        self.id = player_id
        self.x = x
        self.y = y
        self.speed = random.uniform(PLAYER_MIN_SPEED, PLAYER_MAX_SPEED)
        self.heading = random.uniform(0, 2 * math.pi)  # direction, in radians
        self.alive = True
        self.cause_of_death = None

        # Needs are stored in dictionaries keyed by name ("hunger",
        # "thirst", "sleep") so the same code handles all three.
        self.needs = {}
        self.decay_rates = {}
        for name, seconds in NEED_SECONDS_TO_EMPTY.items():
            self.needs[name] = NEED_MAX
            # Amount lost per frame if the need should empty in `seconds`.
            base_rate = NEED_MAX / (seconds * FPS)
            # Scale by a random factor, e.g. 0.75-1.25, so players differ.
            variation = random.uniform(1 - NEED_RATE_VARIATION, 1 + NEED_RATE_VARIATION)
            self.decay_rates[name] = base_rate * variation

    def move(self):
        # Nudge the heading slightly instead of picking a brand new
        # random direction each frame — this is what makes the path
        # look like organic wandering rather than jittery noise.
        self.heading += random.uniform(-WANDER_TURN_RATE, WANDER_TURN_RATE)
        # Keep the heading between 0 and 2*pi so it never grows without
        # limit. This matters later when comparing it to a target angle.
        self.heading %= 2 * math.pi

        self.x += math.cos(self.heading) * self.speed
        self.y += math.sin(self.heading) * self.speed

        # Bounce off the arena walls by reflecting the heading
        if self.x < PLAYER_RADIUS or self.x > SCREEN_WIDTH - PLAYER_RADIUS:
            self.heading = math.pi - self.heading
            self.x = max(PLAYER_RADIUS, min(self.x, SCREEN_WIDTH - PLAYER_RADIUS))
        if self.y < PLAYER_RADIUS or self.y > SCREEN_HEIGHT - PLAYER_RADIUS:
            self.heading = -self.heading
            self.y = max(PLAYER_RADIUS, min(self.y, SCREEN_HEIGHT - PLAYER_RADIUS))

    def update_needs(self):
        """Lower every need by this player's decay rate. The player dies
        the moment any need reaches 0."""
        for name in self.needs:
            self.needs[name] -= self.decay_rates[name]
            if self.needs[name] <= 0:
                self.needs[name] = 0
                self.alive = False
                self.cause_of_death = name
                return  # already dead, no need to check the rest

    def draw(self, screen):
        pygame.draw.circle(
            screen, PLAYER_COLOR, (int(self.x), int(self.y)), PLAYER_RADIUS
        )
        self.draw_warnings(screen)

    def draw_warnings(self, screen):
        """Draw a small colored dot above the player for each need below
        the warning threshold. Each need has a fixed slot (left, middle,
        right) so a given color always appears in the same place."""
        dot_y = int(self.y - PLAYER_RADIUS - WARNING_DOT_OFFSET_Y)
        for slot, name in enumerate(self.needs):
            if self.needs[name] < NEED_WARNING_THRESHOLD:
                # slot 0, 1, 2 -> offset -1, 0, +1 spacings from center
                dot_x = int(self.x + (slot - 1) * WARNING_DOT_SPACING)
                pygame.draw.circle(
                    screen, NEED_WARNING_COLORS[name], (dot_x, dot_y), WARNING_DOT_RADIUS
                )
