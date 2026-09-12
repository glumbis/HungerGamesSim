import math
import random

import pygame
from config import (
    PLAYER_RADIUS, PLAYER_COLOR,
    PLAYER_MIN_SPEED, PLAYER_MAX_SPEED, WANDER_TURN_RATE,
    STEER_TURN_RATE, STEER_SNAP_DISTANCE,
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    NEED_MAX, NEED_WARNING_THRESHOLD, NEED_SECONDS_TO_EMPTY,
    NEED_RATE_VARIATION, NEED_WARNING_COLORS,
    WARNING_DOT_RADIUS, WARNING_DOT_SPACING, WARNING_DOT_OFFSET_Y,
    LOOT_COUNTS, LOOT_RESTORES, LOOT_RESTORE_AMOUNT, LOOT_USE_THRESHOLD,
    CARRY_LIMITS, VISION_RADIUS, VISION_CIRCLE_COLOR, REST_SECONDS_TO_FULL,
    LOOT_COLORS, STRENGTH_MIN, STRENGTH_MAX,
)
from ai import RESTING, STATE_COLORS
from utils import distance, angle_to, angle_difference

# How much sleep a resting player regains per frame
REST_RATE = NEED_MAX / (REST_SECONDS_TO_FULL * FPS)


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

        # How many of each item the player carries, e.g.
        # {"food": 0, "water": 0, "weapon": 0}
        self.inventory = {kind: 0 for kind in LOOT_COUNTS}

        # AI (set and used by ai.py)
        self.aggression = random.random()  # 0 = very cautious, 1 = very aggressive
        self.state = None           # what the player is doing, e.g. "RESTING"
        self.state_timer = 0        # frames spent in the current state
        self.target = None          # (x, y) to head for, or None to wander
        self.search_point = None    # current exploration point when searching
        self.known_loot = set()     # loot items this player has seen
        self.reactions = {}         # other player in sight -> "fight" or "avoid"
        self.prey = None            # the player being hunted, if any
        self.prey_last_seen = None  # (x, y) where the prey was last in sight
        self.hunt_timer = 0         # frames spent on the current hunt
        self.hunt_cooldown = 0      # frames left before a new hunt may start

        # Combat (set and used by combat.py)
        self.strength = random.uniform(STRENGTH_MIN, STRENGTH_MAX)
        self.kills = 0
        self.killer_id = None       # id of the player who eliminated this one
        self.retreat_timer = 0      # frames left backing off after a fight (can't fight meanwhile)
        self.retreat_from = None    # the opponent being backed away from

    def can_carry(self, kind):
        return self.inventory[kind] < CARRY_LIMITS[kind]

    def move(self):
        if self.state == RESTING:
            return  # resting players stand still

        step = self.speed
        if self.target is None:
            # Wander: nudge the heading slightly instead of picking a brand
            # new random direction each frame — this is what makes the path
            # look like organic wandering rather than jittery noise.
            self.heading += random.uniform(-WANDER_TURN_RATE, WANDER_TURN_RATE)
        else:
            target_x, target_y = self.target
            dist = distance(self.x, self.y, target_x, target_y)
            desired = angle_to(self.x, self.y, target_x, target_y)
            if dist < STEER_SNAP_DISTANCE:
                # Close to the target: face it directly. With a limited turn
                # rate a player could otherwise circle around it forever.
                self.heading = desired
            else:
                # Turn toward the target, but no faster than STEER_TURN_RATE,
                # plus a little random drift so movement still looks organic.
                turn = angle_difference(self.heading, desired)
                turn = max(-STEER_TURN_RATE, min(turn, STEER_TURN_RATE))
                self.heading += turn + random.uniform(-WANDER_TURN_RATE / 3, WANDER_TURN_RATE / 3)
            step = min(self.speed, dist)  # don't overshoot the target

        # Keep the heading between 0 and 2*pi so it never grows without limit
        self.heading %= 2 * math.pi

        self.x += math.cos(self.heading) * step
        self.y += math.sin(self.heading) * step

        # Bounce off the arena walls by reflecting the heading
        if self.x < PLAYER_RADIUS or self.x > SCREEN_WIDTH - PLAYER_RADIUS:
            self.heading = math.pi - self.heading
            self.x = max(PLAYER_RADIUS, min(self.x, SCREEN_WIDTH - PLAYER_RADIUS))
        if self.y < PLAYER_RADIUS or self.y > SCREEN_HEIGHT - PLAYER_RADIUS:
            self.heading = -self.heading
            self.y = max(PLAYER_RADIUS, min(self.y, SCREEN_HEIGHT - PLAYER_RADIUS))

    def update_needs(self):
        """Lower every need by this player's decay rate (sleep recovers
        instead while resting). The player dies the moment any need
        reaches 0."""
        for name in self.needs:
            if name == "sleep" and self.state == RESTING:
                self.needs[name] = min(NEED_MAX, self.needs[name] + REST_RATE)
                continue  # skip the decay below for this need
            self.needs[name] -= self.decay_rates[name]
            if self.needs[name] <= 0:
                self.needs[name] = 0
                self.alive = False
                self.cause_of_death = name
                return  # already dead, no need to check the rest

    def pick_up(self, kind):
        self.inventory[kind] += 1

    def use_supplies(self):
        """Eat or drink a carried item once its need drops below the
        threshold."""
        for kind, need in LOOT_RESTORES.items():
            if self.inventory[kind] > 0 and self.needs[need] < LOOT_USE_THRESHOLD:
                self.inventory[kind] -= 1
                # min() stops the need going above the maximum
                self.needs[need] = min(NEED_MAX, self.needs[need] + LOOT_RESTORE_AMOUNT)

    def draw_vision(self, screen):
        """Debug view: outline of how far this player can see."""
        pygame.draw.circle(
            screen, VISION_CIRCLE_COLOR, (int(self.x), int(self.y)), VISION_RADIUS, 1
        )

    def draw(self, screen, debug=False):
        # In the debug view the dot is colored by state
        color = STATE_COLORS[self.state] if debug else PLAYER_COLOR
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), PLAYER_RADIUS)
        if debug and self.inventory["weapon"] > 0:
            # Red outline = carrying a weapon
            pygame.draw.circle(
                screen, LOOT_COLORS["weapon"], (int(self.x), int(self.y)), PLAYER_RADIUS + 2, 1
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
