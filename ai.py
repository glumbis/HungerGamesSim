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
    WEAPON_FEAR_FACTOR, HUNT_GIVE_UP_SECONDS, HUNT_COOLDOWN_SECONDS,
    RETREAT_DISTANCE,
)
from utils import distance, angle_to

# Player states
RUSH_LOOT = "RUSH_LOOT"         # start: aggressive players run for the central loot
FLEE_OUTWARD = "FLEE_OUTWARD"   # start: cautious players run away from the center
RESTING = "RESTING"             # asleep: standing still, recovering sleep, sees nothing
SEEKING = "SEEKING"             # needs food/water and can see some
SEARCHING = "SEARCHING"         # looking for food/water, or for prey that left sight
HUNTING = "HUNTING"             # chasing a visible player to attack it
AVOIDING = "AVOIDING"           # moving away from another player
GATHERING = "GATHERING"         # no urgent need; collecting visible loot
WANDER = "WANDER"               # nothing to do

# Dot color for each state in the debug view
STATE_COLORS = {
    RUSH_LOOT: (230, 200, 60),      # yellow
    FLEE_OUTWARD: (120, 200, 120),  # green
    RESTING: (120, 120, 255),       # blue
    SEEKING: (240, 150, 60),        # orange
    SEARCHING: (240, 90, 220),      # pink
    HUNTING: (255, 40, 40),         # red
    AVOIDING: (170, 120, 70),       # brown
    GATHERING: (80, 210, 210),      # cyan
    WANDER: (220, 220, 220),        # white
}

# How a player reacts to another player it sees
FIGHT = "fight"
AVOID = "avoid"


def set_state(player, state):
    """Change state and restart the state timer — but only if the state
    actually changes, so the timer keeps counting otherwise."""
    if player.state != state:
        player.state = state
        player.state_timer = 0


def clamp_to_arena(x, y, margin):
    """Move a point inside the arena, at least `margin` from every wall."""
    x = max(margin, min(x, SCREEN_WIDTH - margin))
    y = max(margin, min(y, SCREEN_HEIGHT - margin))
    return x, y


def point_away_from(player, from_x, from_y):
    """A point RETREAT_DISTANCE from the player, directly away from
    (from_x, from_y). If a wall is in the way (the point would end up close
    to the player), try turning 90 degrees either way to slide along it."""
    away = angle_to(from_x, from_y, player.x, player.y)
    for turn in (0, math.pi / 2, -math.pi / 2):
        x, y = clamp_to_arena(
            player.x + math.cos(away + turn) * RETREAT_DISTANCE,
            player.y + math.sin(away + turn) * RETREAT_DISTANCE,
            FLEE_EDGE_MARGIN,
        )
        if distance(player.x, player.y, x, y) > RETREAT_DISTANCE / 2:
            break
    return x, y


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
        # Keep the point well clear of the walls
        player.target = clamp_to_arena(x, y, FLEE_EDGE_MARGIN)


def look_around(player, arena, players):
    """Update the player's memory from what it can see, and return the loot
    items and other living players currently in sight."""
    visible_loot = []
    for item in arena.loot:
        if item.dropped_by is player:
            continue  # it won't pick up its own dropped items, so ignore them
        if distance(player.x, player.y, item.x, item.y) <= VISION_RADIUS:
            visible_loot.append(item)
            player.known_loot.add(item)

    # Forget remembered items the player can now see are gone. We loop over
    # a copy (list(...)) because you cannot remove from a set while looping
    # over that same set.
    for item in list(player.known_loot):
        if item.taken and distance(player.x, player.y, item.x, item.y) <= VISION_RADIUS:
            player.known_loot.discard(item)

    visible_players = [
        other for other in players
        if other is not player and other.alive
        and distance(player.x, player.y, other.x, other.y) <= VISION_RADIUS
    ]
    return visible_loot, visible_players


def nearest(player, things):
    """The loot item or player closest to `player`, or None if `things` is
    empty. `key=` tells min() to compare things by their distance."""
    return min(
        things,
        key=lambda thing: distance(player.x, player.y, thing.x, thing.y),
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


def choose_reaction(player, other):
    """Decide once whether to fight or avoid a player that just came into
    sight. A sleeping player is always attacked."""
    if other.state == RESTING:
        return FIGHT
    fight_chance = player.aggression
    if other.inventory["weapon"] > 0 and player.inventory["weapon"] == 0:
        fight_chance *= WEAPON_FEAR_FACTOR  # wary of an armed opponent
    return FIGHT if random.random() < fight_chance else AVOID


def stop_hunting(player, cooldown=False):
    """Forget the current prey. With cooldown=True the player also won't
    start a new hunt for HUNT_COOLDOWN_SECONDS (it avoids players instead)."""
    player.prey = None
    player.prey_last_seen = None
    player.hunt_timer = 0
    if cooldown:
        player.hunt_cooldown = HUNT_COOLDOWN_SECONDS * FPS


def hunt(player, visible_players):
    """Chase the current prey. Returns True if still hunting this frame."""
    prey = player.prey
    if not prey.alive:
        stop_hunting(player)  # prey died some other way
        return False

    player.hunt_timer += 1
    if player.hunt_timer > HUNT_GIVE_UP_SECONDS * FPS:
        stop_hunting(player, cooldown=True)  # chased too long: give up
        return False

    if prey in visible_players:
        player.prey_last_seen = (prey.x, prey.y)
        set_state(player, HUNTING)
        player.target = (prey.x, prey.y)
        return True

    # Prey is out of sight: go to where it was last seen
    if distance(player.x, player.y, *player.prey_last_seen) > ARRIVE_DISTANCE:
        set_state(player, SEARCHING)
        player.target = player.prey_last_seen
        return True
    stop_hunting(player, cooldown=True)  # reached that spot, prey is gone
    return False


def react_to_players(player, visible_players, need):
    """Every player in sight is either fought or avoided. Returns True if
    the player is hunting or avoiding this frame."""
    # Keep reactions only for players still in sight (a dictionary
    # comprehension builds a new dictionary from the old one)
    player.reactions = {other: reaction for other, reaction in player.reactions.items()
                        if other in visible_players}
    for other in visible_players:
        if other not in player.reactions or other.state == RESTING:
            player.reactions[other] = choose_reaction(player, other)

    # Continue an ongoing hunt. If the prey is out of sight and the player
    # has an urgent need, the need wins and the hunt is dropped.
    if player.prey is not None:
        if player.prey in visible_players or need is None:
            if hunt(player, visible_players):
                return True
        else:
            stop_hunting(player)

    # Start a new hunt on the nearest player it chose to fight
    if player.hunt_cooldown == 0:
        to_fight = [other for other in visible_players if player.reactions[other] == FIGHT]
        prey = nearest(player, to_fight)
        if prey:
            player.prey = prey
            player.hunt_timer = 0
            if hunt(player, visible_players):
                return True

    # Otherwise move away from the nearest player in sight. (A player that
    # chose to fight but is on hunt cooldown avoids instead.)
    threat = nearest(player, visible_players)
    if threat:
        set_state(player, AVOIDING)
        player.target = point_away_from(player, threat.x, threat.y)
        return True
    return False


def decide(player, arena, players):
    visible_loot, visible_players = look_around(player, arena, players)
    player.state_timer += 1
    if player.hunt_cooldown > 0:
        player.hunt_cooldown -= 1

    # 1. Opening phase: rush or flee until done or time runs out
    if player.state == RUSH_LOOT and player.state_timer < RUSH_DURATION * FPS:
        wanted = [item for item in visible_loot if player.can_carry(item.kind)]
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

    # 2. Just fought and both survived: back away from the opponent
    if player.retreat_timer > 0:
        player.retreat_timer -= 1
        opponent = player.retreat_from
        set_state(player, AVOIDING)
        player.target = point_away_from(player, opponent.x, opponent.y)
        return

    need = most_urgent_need(player)
    asleep = player.state == RESTING and need == "sleep"

    # 3. Players in sight are fought or avoided (a sleeping player sees nothing)
    if not asleep and react_to_players(player, visible_players, need):
        return

    # 4. Urgent needs
    if need == "sleep":
        set_state(player, RESTING)
        player.target = None
        return
    if need is not None:  # "food" or "water"
        in_sight = [item for item in visible_loot if item.kind == need]
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

    # 5. Collect loot in sight that can still be carried
    wanted = [item for item in visible_loot if player.can_carry(item.kind)]
    if wanted:
        set_state(player, GATHERING)
        item = nearest(player, wanted)
        player.target = (item.x, item.y)
        return

    # 6. Nothing to do
    set_state(player, WANDER)
    player.target = None
