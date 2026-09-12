import math
import random

import pygame
from config import (
    PLAYER_RADIUS, PLAYER_COLOR,
    PLAYER_MIN_SPEED, PLAYER_MAX_SPEED, WANDER_TURN_RATE,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)


class Player:
    def __init__(self, player_id, x, y):
        self.id = player_id
        self.x = x
        self.y = y
        self.speed = random.uniform(PLAYER_MIN_SPEED, PLAYER_MAX_SPEED)
        self.heading = random.uniform(0, 2 * math.pi)  # direction, in radians
        # Strength, needs, and inventory get added once we
        # reach the AI and combat steps.

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

    def draw(self, screen):
        pygame.draw.circle(
            screen, PLAYER_COLOR, (int(self.x), int(self.y)), PLAYER_RADIUS
        )