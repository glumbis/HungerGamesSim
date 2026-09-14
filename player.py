import math
import random

import pygame
from config import (
    PLAYER_RADIUS, PLAYER_COLOR,
    PLAYER_MIN_SPEED, PLAYER_MAX_SPEED, WANDER_TURN_RATE,
    STEER_TURN_RATE, STEER_SNAP_DISTANCE,
    WORLD_WIDTH, WORLD_HEIGHT, FPS,
    NEED_MAX, NEED_WARNING_THRESHOLD, NEED_SECONDS_TO_EMPTY,
    NEED_RATE_VARIATION, NEED_WARNING_COLORS,
    WARNING_DOT_RADIUS, WARNING_DOT_SPACING, WARNING_DOT_OFFSET_Y,
    LOOT_COUNTS, LOOT_RESTORES, LOOT_RESTORE_AMOUNT, LOOT_USE_THRESHOLD,
    CARRY_LIMITS, VISION_RADIUS, VISION_CIRCLE_COLOR, REST_SECONDS_TO_FULL,
    LOOT_COLORS, STRENGTH_MIN, STRENGTH_MAX,
    WEAPON_STRENGTH_BONUS, LEADER_RING_COLOR, FOLLOW_LEASH, STATE_SPEED_MULTIPLIERS,
    TEMPERAMENT_WEIGHTS, AGGRESSION_RANGES, ROAMING_WEIGHTS,
    SPRINT_SECONDS, STAMINA_RECOVERY_SECONDS, NAME_MIN_ZOOM, NAME_TEXT_COLOR,
    TERRAIN_SPEED, SAND_THIRST_FACTOR, MARSH_REFILL_SECONDS,
)
from ai import RESTING, HUNTING, AVOIDING, FOLLOWING, STATE_COLORS
from utils import distance, angle_to, angle_difference

# How much sleep a resting player regains per frame
REST_RATE = NEED_MAX / (REST_SECONDS_TO_FULL * FPS)
# How much thirst a player in marsh regains per frame
MARSH_REFILL_RATE = NEED_MAX / (MARSH_REFILL_SECONDS * FPS)


class Player:
    def __init__(self, player_id, x, y, name):
        self.id = player_id
        self.name = name
        self.district = player_id // 2 + 1  # players 0 and 1 are District 1, 2 and 3 are District 2, ...
        self.loner = False          # "no alliance" trait: never allies with anyone (set in main.py)
        self.name_label = None      # the name and district rendered as an image, made the first time it is drawn
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
        # Personality traits, fixed for the whole game. random.choices picks
        # one name using the weights; [0] takes that name out of the list.
        self.temperament = random.choices(
            list(TEMPERAMENT_WEIGHTS), weights=list(TEMPERAMENT_WEIGHTS.values()))[0]
        self.roaming = random.choices(
            list(ROAMING_WEIGHTS), weights=list(ROAMING_WEIGHTS.values()))[0]
        # Aggression (0 = very cautious, 1 = very aggressive) fits the temperament
        low, high = AGGRESSION_RANGES[self.temperament]
        self.aggression = random.uniform(low, high)
        self.state = None           # what the player is doing, e.g. "RESTING"
        self.state_timer = 0        # frames spent in the current state
        self.target = None          # (x, y) to head for, or None to stand still
        self.search_point = None    # current point to search when looking for food/water
        self.explore_point = None   # current point to explore when nothing is urgent
        self.visited_cells = set()  # arena cells (column, row) this player has been in
        self.pause_timer = 0        # frames left standing still to look around
        self.rest_spot = None       # (x, y) by a wall where it intends to sleep
        self.collapsed = False      # True while sleeping on the spot after running out of sleep
        self.avoid_point = None     # (x, y) it is backing away to
        self.avoid_timer = 0        # frames left committed to backing away
        self.placement = None       # final place (1 = winner), set when it dies or wins
        self.death_frame = None     # simulation frame it died on
        self.track_point = None     # estimated waypoint toward an unseen player (leaders)
        self.track_timer = 0        # frames until that direction is re-estimated
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
        self.killer_name = None     # ...and its name
        self.fight = None           # the fight this player is locked in (combat.Fight), if any
        self.stamina = 1.0          # 1 = rested, 0 = exhausted (can't sprint)
        self.heard_fight = None     # (x, y) of the last fight this player heard
        self.heard_timer = 0        # frames left that it still cares about that noise
        self.terrain = "meadow"     # terrain type under the player (updated by ai.look_around)
        self.water_spot = None      # marsh it is heading for to drink (False: none within reach)
        self.tip_target = None      # player the Gamemakers pointed it at after a quiet spell
        self.tip_timer = 0          # frames left to go after that player
        self.retreat_timer = 0      # frames left backing off after a fight (can't fight meanwhile)
        self.retreat_from = None    # the opponent being backed away from

        # Alliances (set and used by alliances.py and ai.py)
        self.alliance = None        # the Alliance this player belongs to, if any
        self.former_allies = set()  # players it will never ally with again
        self.alliance_rolls = set() # players it has already had its one chance to ally with
        self.follow_offset = (0, 0) # this member's spot relative to its leader
        self.visible_loot = []      # what it saw this frame (read by its leader)
        self.visible_players = []

    def can_carry(self, kind):
        return self.inventory[kind] < CARRY_LIMITS[kind]

    def fighting_strength(self):
        """Own strength plus the weapon bonus (without any help from allies)."""
        bonus = WEAPON_STRENGTH_BONUS if self.inventory["weapon"] > 0 else 0
        return self.strength + bonus

    def current_speed(self):
        """How fast the player moves this frame.
        - Urgent states (hunting, avoiding, ...) are faster; see
          STATE_SPEED_MULTIPLIERS. .get(state, 1.0) means "1.0 if not listed".
        - A following member speeds up when its leader does.
        - A leader moves no faster than its slowest member, and at half that
          while calm and a member has fallen behind, so the group stays together.
        - An exhausted player (no stamina left) can't sprint.
        - Some terrain (marsh) slows everyone down."""
        multiplier = STATE_SPEED_MULTIPLIERS.get(self.state, 1.0)
        speed = self.speed
        if self.alliance is not None:
            leader = self.alliance.leader
            if leader is not self:
                if self.state == FOLLOWING:
                    multiplier = max(multiplier, STATE_SPEED_MULTIPLIERS.get(leader.state, 1.0))
            else:
                members = self.alliance.members
                speed = min(member.speed for member in members)
                straggling = any(
                    distance(self.x, self.y, member.x, member.y) > FOLLOW_LEASH for member in members
                )
                if straggling and self.state not in (HUNTING, AVOIDING):
                    multiplier *= 0.5
        if self.stamina <= 0:
            multiplier = min(multiplier, 1.0)  # exhausted: no sprinting
        return speed * multiplier * TERRAIN_SPEED.get(self.terrain, 1.0)

    def move(self):
        # Stamina: sprinting (moving in a fast state) uses it up, anything
        # else slowly restores it
        sprinting = self.target is not None and STATE_SPEED_MULTIPLIERS.get(self.state, 1.0) > 1
        if sprinting:
            self.stamina = max(0.0, self.stamina - 1 / (SPRINT_SECONDS * FPS))
        else:
            self.stamina = min(1.0, self.stamina + 1 / (STAMINA_RECOVERY_SECONDS * FPS))

        if self.state == RESTING:
            return  # resting players stand still

        if self.target is None:
            return  # no target: stand still (e.g. pausing to look around)

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
        step = min(self.current_speed(), dist)  # don't overshoot the target

        # Keep the heading between 0 and 2*pi so it never grows without limit
        self.heading %= 2 * math.pi

        self.x += math.cos(self.heading) * step
        self.y += math.sin(self.heading) * step

        # Bounce off the arena walls by reflecting the heading
        if self.x < PLAYER_RADIUS or self.x > WORLD_WIDTH - PLAYER_RADIUS:
            self.heading = math.pi - self.heading
            self.x = max(PLAYER_RADIUS, min(self.x, WORLD_WIDTH - PLAYER_RADIUS))
        if self.y < PLAYER_RADIUS or self.y > WORLD_HEIGHT - PLAYER_RADIUS:
            self.heading = -self.heading
            self.y = max(PLAYER_RADIUS, min(self.y, WORLD_HEIGHT - PLAYER_RADIUS))

    def update_needs(self):
        """Lower every need by this player's decay rate (sleep recovers
        instead while resting). The player dies the moment any need
        reaches 0."""
        for name in self.needs:
            if name == "sleep" and self.state == RESTING:
                self.needs[name] = min(NEED_MAX, self.needs[name] + REST_RATE)
                continue  # skip the decay below for this need
            if name == "thirst" and self.terrain == "marsh":
                self.needs[name] = min(NEED_MAX, self.needs[name] + MARSH_REFILL_RATE)
                continue  # marsh water: thirst goes up instead of down
            rate = self.decay_rates[name]
            if name == "thirst" and self.terrain == "sand":
                rate *= SAND_THIRST_FACTOR  # hot, open sand makes players thirsty faster
            self.needs[name] -= rate
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

    def draw_vision(self, screen, camera):
        """Debug view: outline of how far this player can see."""
        pygame.draw.circle(screen, VISION_CIRCLE_COLOR,
                           camera.world_to_screen(self.x, self.y, screen),
                           camera.size(VISION_RADIUS), 1)

    def draw(self, screen, camera, name_font, debug=False):
        center = camera.world_to_screen(self.x, self.y, screen)
        # Skip players outside the window (the extra 40 px keeps rings visible at the edge)
        if not screen.get_rect().inflate(40, 40).collidepoint(center):
            return
        radius = camera.size(PLAYER_RADIUS, minimum=2)

        # Debug view: dot colored by state. Normal view: allies share a color.
        if debug:
            color = STATE_COLORS[self.state]
        elif self.alliance is not None:
            color = self.alliance.color
        else:
            color = PLAYER_COLOR
        pygame.draw.circle(screen, color, center, radius)
        if self.alliance is not None and self.alliance.leader is self:
            # Ring = alliance leader (white normally, alliance color in debug view)
            ring_color = self.alliance.color if debug else LEADER_RING_COLOR
            pygame.draw.circle(screen, ring_color, center, radius + camera.size(4, 2), 1)
        if debug and self.inventory["weapon"] > 0:
            # Red outline = carrying a weapon
            pygame.draw.circle(screen, LOOT_COLORS["weapon"], center, radius + camera.size(2, 1), 1)
        self.draw_warnings(screen, camera, center, radius)

        # The name, small, above the warning dots (hidden when zoomed far out)
        if camera.zoom >= NAME_MIN_ZOOM:
            if self.name_label is None:
                self.name_label = name_font.render(f"{self.name} ({self.district})", True, NAME_TEXT_COLOR)
            above_dots = center[1] - radius - camera.size(WARNING_DOT_OFFSET_Y, 2) \
                - camera.size(WARNING_DOT_RADIUS, 1) - 2
            screen.blit(self.name_label, self.name_label.get_rect(midbottom=(center[0], above_dots)))

    def draw_warnings(self, screen, camera, center, radius):
        """Draw a small colored dot above the player for each need below
        the warning threshold. Each need has a fixed slot (left, middle,
        right) so a given color always appears in the same place."""
        dot_radius = camera.size(WARNING_DOT_RADIUS, 1)
        spacing = camera.size(WARNING_DOT_SPACING, 3)
        dot_y = center[1] - radius - camera.size(WARNING_DOT_OFFSET_Y, 2)
        for slot, name in enumerate(self.needs):
            if self.needs[name] < NEED_WARNING_THRESHOLD:
                # slot 0, 1, 2 -> offset -1, 0, +1 spacings from the center
                dot_x = center[0] + (slot - 1) * spacing
                pygame.draw.circle(screen, NEED_WARNING_COLORS[name], (dot_x, dot_y), dot_radius)
