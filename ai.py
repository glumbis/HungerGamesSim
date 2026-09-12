"""Decision-making. Every frame, decide() sets each player's `state` (what
it is doing) and `target` (the point it is heading for, or None to wander).
Player.move() then carries that out."""
import math
import random

from config import (
    FPS, SCREEN_WIDTH, SCREEN_HEIGHT,
    VISION_RADIUS, ARRIVE_DISTANCE, RUSH_DURATION, FLEE_DURATION,
    FLEE_DISTANCE, FLEE_EDGE_MARGIN,
    SEEK_THRESHOLD, REST_THRESHOLD, REST_UNTIL, LOOT_RESTORES,
)
from utils import distance, angle_to

# Player states
RUSH_LOOT = "RUSH_LOOT"         # start: aggressive players run for the central loot
FLEE_OUTWARD = "FLEE_OUTWARD"   # start: cautious players run away from the center
RESTING = "RESTING"             # standing still, recovering sleep
SEEKING = "SEEKING"             # needs food/water and can see some
SEARCHING = "SEARCHING"         # needs food/water but none in sight
GATHERING = "GATHERING"         # no urgent need; collecting visible loot
WANDER = "WANDER"               # nothing to do

# Dot color for each state in the debug view
STATE_COLORS = {
    RUSH_LOOT: (230, 200, 60),      # yellow
    FLEE_OUTWARD: (120, 200, 120),  # green
    RESTING: (120, 120, 255),       # blue
    SEEKING: (240, 90, 90),         # red
    SEARCHING: (240, 90, 220),      # pink
    GATHERING: (80, 210, 210),      # cyan
    WANDER: (220, 220, 220),        # white
}


def set_state(player, state):
    """Change state and restart the state timer — but only if the state
    actually changes, so the timer keeps counting otherwise."""
    if player.state != state:
        player.state = state
        player.state_timer = 0


def choose_opening_state(player, arena):
    """At the start, a player either rushes the center or flees outward.
    The higher its aggression (0-1), the more likely it rushes."""
    if random.random() < player.aggression:
        set_state(player, RUSH_LOOT)
    else:
        set_state(player, FLEE_OUTWARD)
        # Aim for a point roughly away from the center (with a little random
        # variation in direction), FLEE_DISTANCE from the center
        away = angle_to(arena.center_x, arena.center_y, player.x, player.y)
        away += random.uniform(-0.3, 0.3)
        x = arena.center_x + math.cos(away) * FLEE_DISTANCE
        y = arena.center_y + math.sin(away) * FLEE_DISTANCE
        # Clamp the point so it stays well clear of the walls
        margin = FLEE_EDGE_MARGIN
        x = max(margin, min(x, SCREEN_WIDTH - margin))
        y = max(margin, min(y, SCREEN_HEIGHT - margin))
        player.target = (x, y)


def look_around(player, arena):
    """Update the player's memory from what it can see, and return the
    loot items currently in sight."""
    visible = []
    for item in arena.loot:
        if distance(player.x, player.y, item.x, item.y) <= VISION_RADIUS:
            visible.append(item)
            player.known_loot.add(item)

    # Forget remembered items the player can now see are gone. We loop over
    # a copy (list(...)) because you cannot remove from a set while looping
    # over that same set.
    for item in list(player.known_loot):
        if item.taken and distance(player.x, player.y, item.x, item.y) <= VISION_RADIUS:
            player.known_loot.discard(item)
    return visible


def nearest(player, items):
    """The item closest to the player, or None if `items` is empty.
    `key=` tells min() to compare items by their distance to the player."""
    return min(
        items,
        key=lambda item: distance(player.x, player.y, item.x, item.y),
        default=None,
    )


def most_urgent_need(player):
    """Return "sleep", "food", "water", or None if nothing needs doing.

    - Sleep counts when it is low, or while already resting and not yet
      rested enough.
    - Food/water counts when hunger/thirst is low AND nothing suitable is
      carried (if something is carried, use_supplies() handles it).
    If several count, the one with the lowest value wins."""
    urgent = {}  # what is needed -> current value of that need
    sleep = player.needs["sleep"]
    if sleep < REST_THRESHOLD or (player.state == RESTING and sleep < REST_UNTIL):
        urgent["sleep"] = sleep
    for kind, need in LOOT_RESTORES.items():  # ("food", "hunger"), ("water", "thirst")
        if player.needs[need] < SEEK_THRESHOLD and player.inventory[kind] == 0:
            urgent[kind] = player.needs[need]

    if not urgent:
        return None
    return min(urgent, key=urgent.get)  # the key with the smallest value


def decide(player, arena):
    visible = look_around(player, arena)
    player.state_timer += 1

    # 1. Opening phase: keep rushing or fleeing until time runs out
    if player.state == RUSH_LOOT and player.state_timer < RUSH_DURATION * FPS:
        wanted = [item for item in visible if player.can_carry(item.kind)]
        item = nearest(player, wanted)
        if item:
            player.target = (item.x, item.y)
            return
        center_dist = distance(player.x, player.y, arena.center_x, arena.center_y)
        if center_dist > VISION_RADIUS:
            player.target = (arena.center_x, arena.center_y)
            return
        # The center is in sight and there is nothing left to grab: the rush
        # is over, so fall through to the normal decisions below.
    if player.state == FLEE_OUTWARD and player.state_timer < FLEE_DURATION * FPS:
        if distance(player.x, player.y, *player.target) > ARRIVE_DISTANCE:
            return  # still on the way to the flee point
        # Arrived at the flee point: fall through to the normal decisions below.

    # 2. Urgent needs override everything else
    need = most_urgent_need(player)
    if need == "sleep":
        set_state(player, RESTING)
        player.target = None
        return
    if need is not None:  # "food" or "water"
        in_sight = [item for item in visible if item.kind == need]
        if in_sight:
            set_state(player, SEEKING)
            item = nearest(player, in_sight)
            player.target = (item.x, item.y)
            return

        set_state(player, SEARCHING)
        remembered = [item for item in player.known_loot if item.kind == need]
        if remembered:
            # Head for the closest remembered item (it may already be gone)
            item = nearest(player, remembered)
            player.target = (item.x, item.y)
        else:
            # Nothing known: explore by walking to random points
            if player.search_point is None or distance(
                    player.x, player.y, *player.search_point) < ARRIVE_DISTANCE:
                player.search_point = arena.random_point(ARRIVE_DISTANCE)
            player.target = player.search_point
        return

    # 3. No urgent need: collect loot in sight that can still be carried
    wanted = [item for item in visible if player.can_carry(item.kind)]
    if wanted:
        set_state(player, GATHERING)
        item = nearest(player, wanted)
        player.target = (item.x, item.y)
        return

    # 4. Nothing to do
    set_state(player, WANDER)
    player.target = None
