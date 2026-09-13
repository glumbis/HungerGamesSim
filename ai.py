"""Decision-making. Every frame, decide() sets each player's `state` (what
it is doing) and `target` (the point it is heading for, or None to stand
still). Player.move() then carries that out."""
import math
import random

import alliances
from config import (
    FPS, SCREEN_WIDTH, SCREEN_HEIGHT,
    VISION_RADIUS, ARRIVE_DISTANCE, RUSH_DURATION, FLEE_DURATION,
    FLEE_DISTANCE, FLEE_EDGE_MARGIN,
    SEEK_THRESHOLD, REST_THRESHOLD, REST_UNTIL, LOOT_RESTORES,
    WEAPON_FEAR_FACTOR, HUNT_GIVE_UP_SECONDS, HUNT_COOLDOWN_SECONDS,
    RETREAT_DISTANCE, FOLLOW_SPREAD, FOLLOW_LEASH,
    EXPLORE_CELL_SIZE, EXPLORE_PAUSE_MIN, EXPLORE_PAUSE_MAX, SHELTER_WALL_MARGIN,
    STALK_DISTANCE, ALLIANCE_SENSE_RADIUS, ALLIANCE_AGGRESSION_BONUS,
    TRACK_RADIUS, TRACK_STEP, TRACK_ANGLE_NOISE, TRACK_UPDATE_SECONDS, TRACK_MIN_FIGHT_CHANCE,
    EXPLORER_PAUSE_FACTOR, SHOWDOWN_PLAYERS, EDGE_BAND,
)
from utils import distance, angle_to

# Player states
RUSH_LOOT = "RUSH_LOOT"         # start: aggressive players run for the central loot
FLEE_OUTWARD = "FLEE_OUTWARD"   # start: cautious players run away from the center
SHELTERING = "SHELTERING"       # tired: walking to a quiet spot by a wall to sleep
RESTING = "RESTING"             # asleep: standing still, recovering sleep, sees nothing
SEEKING = "SEEKING"             # needs food/water and can see some
SEARCHING = "SEARCHING"         # looking for food/water, or for prey that left sight
HUNTING = "HUNTING"             # chasing a visible player to attack it
AVOIDING = "AVOIDING"           # moving away from another player
GATHERING = "GATHERING"         # no urgent need; collecting visible loot
FOLLOWING = "FOLLOWING"         # alliance member staying near its leader
TRACKING = "TRACKING"           # aggressive alliance heading roughly toward unseen players
EXPLORING = "EXPLORING"         # nothing urgent: heading for unvisited parts of the arena

# Dot color for each state in the debug view
STATE_COLORS = {
    RUSH_LOOT: (230, 200, 60),      # yellow
    FLEE_OUTWARD: (120, 200, 120),  # green
    SHELTERING: (90, 150, 200),     # steel blue
    RESTING: (120, 120, 255),       # blue
    SEEKING: (240, 150, 60),        # orange
    SEARCHING: (240, 90, 220),      # pink
    HUNTING: (255, 40, 40),         # red
    AVOIDING: (170, 120, 70),       # brown
    GATHERING: (80, 210, 210),      # cyan
    FOLLOWING: (200, 160, 255),     # lavender
    TRACKING: (255, 130, 90),       # coral
    EXPLORING: (220, 220, 220),     # white
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


def cell_of(x, y):
    """Which exploration cell (column, row) a point lies in. // is whole-number division."""
    return int(x // EXPLORE_CELL_SIZE), int(y // EXPLORE_CELL_SIZE)


def choose_explore_point(player, roaming=None):
    """A random point in a cell this player has not visited yet. Which cells
    count depends on its roaming trait (or on `roaming`, if given):
    - "edge": only cells along the arena walls, one of the three nearest
    - "explorer": any unvisited cell, however far away
    - "normal": one of the three nearest unvisited cells
    Once every candidate cell has been visited, it starts over."""
    roaming = roaming or player.roaming  # `or`: use player.roaming if roaming is None
    cols = math.ceil(SCREEN_WIDTH / EXPLORE_CELL_SIZE)
    rows = math.ceil(SCREEN_HEIGHT / EXPLORE_CELL_SIZE)
    candidates = [(col, row) for col in range(cols) for row in range(rows)]
    if roaming == "edge":
        candidates = [(col, row) for col, row in candidates
                      if col in (0, cols - 1) or row in (0, rows - 1)]
    unvisited = [cell for cell in candidates if cell not in player.visited_cells]
    if not unvisited:
        # All candidates visited: forget those visits and start over
        player.visited_cells -= set(candidates)  # -= removes these cells from the set
        unvisited = candidates

    def distance_to_cell(cell):
        col, row = cell
        center_x = (col + 0.5) * EXPLORE_CELL_SIZE
        center_y = (row + 0.5) * EXPLORE_CELL_SIZE
        return distance(player.x, player.y, center_x, center_y)

    if roaming == "explorer":
        col, row = random.choice(unvisited)
    else:
        unvisited.sort(key=distance_to_cell)  # nearest cells first
        col, row = random.choice(unvisited[:3])
    x = random.uniform(col * EXPLORE_CELL_SIZE, (col + 1) * EXPLORE_CELL_SIZE)
    y = random.uniform(row * EXPLORE_CELL_SIZE, (row + 1) * EXPLORE_CELL_SIZE)

    if roaming == "edge":
        # Hug the wall: move the point to within EDGE_BAND of the nearest wall.
        # The * in uniform(*EDGE_BAND) unpacks the (min, max) pair into two arguments.
        gap = random.uniform(*EDGE_BAND)
        walls = [(x, "left"), (SCREEN_WIDTH - x, "right"), (y, "top"), (SCREEN_HEIGHT - y, "bottom")]
        nearest_wall = min(walls)[1]  # the smallest distance wins
        if nearest_wall == "left":
            x = gap
        elif nearest_wall == "right":
            x = SCREEN_WIDTH - gap
        elif nearest_wall == "top":
            y = gap
        else:
            y = SCREEN_HEIGHT - gap
        return clamp_to_arena(x, y, EDGE_BAND[0])
    return clamp_to_arena(x, y, FLEE_EDGE_MARGIN)


def explore(player):
    """Walk to a part of the arena this player hasn't visited, pause on
    arrival to look around, then pick the next one."""
    set_state(player, EXPLORING)
    if player.pause_timer > 0:
        player.pause_timer -= 1
        player.target = None  # stand still while looking around
        return
    if player.explore_point is not None and \
            distance(player.x, player.y, *player.explore_point) < ARRIVE_DISTANCE:
        player.explore_point = None
        pause = random.uniform(EXPLORE_PAUSE_MIN, EXPLORE_PAUSE_MAX)
        if player.roaming == "explorer":
            pause *= EXPLORER_PAUSE_FACTOR  # explorers don't linger
        player.pause_timer = int(pause * FPS)
        player.target = None
        return
    if player.explore_point is None:
        player.explore_point = choose_explore_point(player)
    player.target = player.explore_point


def shelter_spot(player):
    """A spot SHELTER_WALL_MARGIN from the wall nearest to the player, away
    from the busy center. Each option is (distance to that wall, spot)."""
    options = [
        (player.x, (SHELTER_WALL_MARGIN, player.y)),                                  # left
        (SCREEN_WIDTH - player.x, (SCREEN_WIDTH - SHELTER_WALL_MARGIN, player.y)),    # right
        (player.y, (player.x, SHELTER_WALL_MARGIN)),                                  # top
        (SCREEN_HEIGHT - player.y, (player.x, SCREEN_HEIGHT - SHELTER_WALL_MARGIN)),  # bottom
    ]
    closest = min(options, key=lambda option: option[0])
    return closest[1]


def choose_opening_state(player, arena):
    """At the start, a player either rushes the center or flees outward.
    Killers always rush and cowards always flee; for everyone else, the
    higher the aggression (0-1), the more likely it rushes."""
    if player.temperament == "killer":
        rushes = True
    elif player.temperament == "coward":
        rushes = False
    else:
        rushes = random.random() < player.aggression

    if rushes:
        set_state(player, RUSH_LOOT)
    else:
        set_state(player, FLEE_OUTWARD)
        # Aim for a point roughly away from the center (with a little random
        # variation in direction). Edge dwellers run all the way to the wall.
        away = angle_to(arena.center_x, arena.center_y, player.x, player.y)
        away += random.uniform(-0.3, 0.3)
        flee_distance = FLEE_DISTANCE if player.roaming != "edge" else max(SCREEN_WIDTH, SCREEN_HEIGHT)
        x = arena.center_x + math.cos(away) * flee_distance
        y = arena.center_y + math.sin(away) * flee_distance
        # Keep the point well clear of the walls
        player.target = clamp_to_arena(x, y, FLEE_EDGE_MARGIN)


def look_around(player, arena, players):
    """Update the player's memory from what it can see, and store the loot
    items and non-allied living players currently in sight on the player
    (as visible_loot and visible_players)."""
    player.visited_cells.add(cell_of(player.x, player.y))

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

    player.visible_loot = visible_loot
    # Alliance members keep watch for each other, so they notice other
    # players from further away than a player on its own would
    radius = ALLIANCE_SENSE_RADIUS if player.alliance is not None else VISION_RADIUS
    player.visible_players = [
        other for other in players
        if other is not player and other.alive and not is_ally(player, other)
        and distance(player.x, player.y, other.x, other.y) <= radius
    ]


def is_ally(player, other):
    return player.alliance is not None and other.alliance is player.alliance


def shared_view(leader):
    """Everything any member of the leader's alliance can see, without
    duplicates, plus everything any member remembers. This is how the
    leader takes the whole group into account."""
    members = leader.alliance.members
    loot, others, known = [], [], set()
    for member in members:
        for item in member.visible_loot:
            # Skip items already taken, and items the leader dropped (it
            # won't pick those up)
            if not item.taken and item.dropped_by is not leader and item not in loot:
                loot.append(item)
        for other in member.visible_players:
            if other.alive and not is_ally(leader, other) and other not in others:
                others.append(other)
        for item in member.known_loot:
            if item.dropped_by is leader:
                continue
            # If any member can see a remembered item is gone, the group knows
            if item.taken and any(
                    distance(m.x, m.y, item.x, item.y) <= VISION_RADIUS for m in members):
                continue
            known.add(item)
    return loot, others, known


def nearest(player, things):
    """The loot item or player closest to `player`, or None if `things` is
    empty. `key=` tells min() to compare things by their distance."""
    return min(
        things,
        key=lambda thing: distance(player.x, player.y, thing.x, thing.y),
        default=None,
    )


def most_urgent_need(members, resting):
    """Return "sleep", "food", "water", or None if nothing needs doing.
    `members` is [player] for a player on its own, or every member of an
    alliance, so a leader acts on the needs of the whole group.

    - Sleep counts when anyone is low, or while already resting and not
      everyone has rested enough.
    - Food/water counts when anyone's hunger/thirst is low AND nobody
      carries anything to fix it (carried items are used or shared instead).
    If several count, the one with the lowest value wins."""
    urgent = {}  # what is needed -> lowest value of that need in the group
    lowest_sleep = min(member.needs["sleep"] for member in members)
    if lowest_sleep < REST_THRESHOLD or (resting and lowest_sleep < REST_UNTIL):
        urgent["sleep"] = lowest_sleep
    for kind, need in LOOT_RESTORES.items():  # ("food", "hunger"), ("water", "thirst")
        lowest = min(member.needs[need] for member in members)
        carried = sum(member.inventory[kind] for member in members)
        if lowest < SEEK_THRESHOLD and carried == 0:
            urgent[kind] = lowest

    if not urgent:
        return None
    return min(urgent, key=urgent.get)  # the key with the smallest value


def fight_chance(player, other=None):
    """How likely `player` (or the alliance it leads) is to choose a fight.
    Fixed traits come first:
    - bloodthirsty alliances and killers always fight (1.0)
    - defensive alliances and cowards never choose to (0.0)
    Otherwise: aggression, plus a bonus for every extra alliance member,
    lowered if `other` is armed and nobody in the group is. Never above 1."""
    if player.alliance is not None:
        if player.alliance.style == "bloodthirsty":
            return 1.0
        if player.alliance.style == "defensive":
            return 0.0
    else:
        if player.temperament == "killer":
            return 1.0
        if player.temperament == "coward":
            return 0.0

    group = player.alliance.members if player.alliance else [player]
    chance = player.aggression + ALLIANCE_AGGRESSION_BONUS * (len(group) - 1)
    group_armed = any(member.inventory["weapon"] > 0 for member in group)
    if other is not None and other.inventory["weapon"] > 0 and not group_armed:
        chance *= WEAPON_FEAR_FACTOR  # wary of an armed opponent
    return min(chance, 1.0)


def choose_reaction(player, other):
    """Decide once whether to fight or avoid a player that just came into
    sight. A sleeping player is always attacked."""
    if other.state == RESTING:
        return FIGHT
    return FIGHT if random.random() < fight_chance(player, other) else AVOID


def stop_hunting(player, cooldown=False):
    """Forget the current prey. With cooldown=True the player also won't
    start a new hunt for HUNT_COOLDOWN_SECONDS (it avoids players instead)."""
    player.prey = None
    player.prey_last_seen = None
    player.hunt_timer = 0
    if cooldown:
        player.hunt_cooldown = HUNT_COOLDOWN_SECONDS * FPS


def chase_target(player, prey):
    """Where a hunter heads. If the hunter or its prey has only just fought,
    no new fight can start yet, so the hunter waits close by (None = stand
    still) instead of standing right on top of the prey."""
    if (prey.retreat_timer > 0 or player.retreat_timer > 0) and \
            distance(player.x, player.y, prey.x, prey.y) < STALK_DISTANCE:
        return None
    return (prey.x, prey.y)


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
        player.target = chase_target(player, prey)
        return True

    # Prey is out of sight: go to where it was last seen. (A player that
    # joined a group hunt may never have seen the prey itself.)
    if player.prey_last_seen is None:
        stop_hunting(player)
        return False
    if distance(player.x, player.y, *player.prey_last_seen) > ARRIVE_DISTANCE:
        set_state(player, SEARCHING)
        player.target = player.prey_last_seen
        return True
    stop_hunting(player, cooldown=True)  # reached that spot, prey is gone
    return False


def face_to_face(player, other):
    """True if `player`, or anyone in its alliance, is within normal vision
    of `other`. Alliances are only offered face to face — not to players an
    alliance merely noticed from further away."""
    group = player.alliance.members if player.alliance else [player]
    return any(distance(member.x, member.y, other.x, other.y) <= VISION_RADIUS
               for member in group)


def react_to_players(player, visible_players, need):
    """Every non-allied player in sight is allied with, fought or avoided.
    Called for players on their own and for alliance leaders. Returns True
    if the player is busy with this for the current frame."""
    # Keep reactions only for players still in sight (a dictionary
    # comprehension builds a new dictionary from the old one)
    player.reactions = {other: reaction for other, reaction in player.reactions.items()
                        if other in visible_players}
    for other in visible_players:
        if other not in player.reactions:
            # First sighting: maybe team up, otherwise choose fight or avoid
            if other.state != RESTING and face_to_face(player, other) \
                    and alliances.try_to_ally(player, other):
                return True  # the groups changed; decide again next frame
            player.reactions[other] = choose_reaction(player, other)
        elif other.state == RESTING:
            player.reactions[other] = FIGHT  # fell asleep in sight: attack
        elif player.reactions[other] == FIGHT and fight_chance(player, other) == 0.0:
            # A coward (or defensive alliance) only attacks while the other
            # sleeps: once it wakes up, go back to avoiding it
            player.reactions[other] = AVOID
            if player.prey is other:
                stop_hunting(player)

    # An alliance defends its members: anyone in sight who is hunting one of
    # them becomes the group's target, even during a hunt cooldown
    if player.alliance is not None and player.prey is None:
        attackers = [other for other in visible_players
                     if other.prey is not None and other.prey.alliance is player.alliance]
        attacker = nearest(player, attackers)
        if attacker:
            player.reactions[attacker] = FIGHT
            player.prey = attacker
            player.hunt_timer = 0

    # Continue an ongoing hunt. If the prey is out of sight and there is an
    # urgent need, the need wins and the hunt is dropped.
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


def track(leader, players):
    """An aggressive player or alliance (killers, bloodthirsty alliances, or
    anyone whose fight chance is high enough) heads roughly toward the
    nearest non-ally within TRACK_RADIUS, even one it can't see. It doesn't know exactly
    where that player is, so it aims in an estimated direction (with random
    error) and re-estimates every few seconds. Returns True if tracking."""
    if fight_chance(leader) < TRACK_MIN_FIGHT_CHANCE:
        return False
    candidates = [other for other in players
                  if other is not leader and other.alive and not is_ally(leader, other)
                  and distance(leader.x, leader.y, other.x, other.y) <= TRACK_RADIUS]
    quarry = nearest(leader, candidates)
    if quarry is None:
        return False

    if leader.state != TRACKING:
        leader.track_point = None  # just started: estimate a fresh direction
    leader.track_timer -= 1
    arrived = leader.track_point is not None and \
        distance(leader.x, leader.y, *leader.track_point) < ARRIVE_DISTANCE
    if leader.track_point is None or leader.track_timer <= 0 or arrived:
        direction = angle_to(leader.x, leader.y, quarry.x, quarry.y)
        direction += random.uniform(-TRACK_ANGLE_NOISE, TRACK_ANGLE_NOISE)
        step = min(TRACK_STEP, distance(leader.x, leader.y, quarry.x, quarry.y))
        leader.track_point = clamp_to_arena(
            leader.x + math.cos(direction) * step,
            leader.y + math.sin(direction) * step,
            ARRIVE_DISTANCE,
        )
        leader.track_timer = TRACK_UPDATE_SECONDS * FPS

    set_state(leader, TRACKING)
    leader.target = leader.track_point
    return True


def follow_leader(player):
    """Alliance members don't make their own plans: they join the leader's
    hunts, sleep when it sleeps, and otherwise stay close to it."""
    leader = player.alliance.leader

    # Join the leader's hunt — only while the leader is actually chasing,
    # not while the group is backing off or searching
    if leader.state == HUNTING and leader.prey is not None and leader.prey.alive \
            and leader.prey in player.visible_players:
        player.prey = leader.prey
        set_state(player, HUNTING)
        player.target = chase_target(player, leader.prey)
        return
    player.prey = None

    to_leader = distance(player.x, player.y, leader.x, leader.y)

    # Sleep when the leader sleeps, once close to it
    if leader.state == RESTING and to_leader <= FOLLOW_SPREAD * 2:
        set_state(player, RESTING)
        player.target = None
        return

    # Collect loot close to the leader, unless the group is busy
    if leader.state not in (RESTING, SHELTERING, HUNTING, AVOIDING, TRACKING):
        wanted = [item for item in player.visible_loot
                  if player.can_carry(item.kind)
                  and distance(item.x, item.y, leader.x, leader.y) <= FOLLOW_LEASH]
        item = nearest(player, wanted)
        if item:
            set_state(player, GATHERING)
            player.target = (item.x, item.y)
            return

    # Otherwise keep to the member's own spot next to the leader
    set_state(player, FOLLOWING)
    offset_x, offset_y = player.follow_offset
    spot = clamp_to_arena(leader.x + offset_x, leader.y + offset_y, ARRIVE_DISTANCE)
    if distance(player.x, player.y, *spot) >= ARRIVE_DISTANCE:
        player.target = spot
        return

    # At its spot: stand still for a moment, then pick a new spot nearby
    if player.pause_timer == 0:
        player.pause_timer = int(random.uniform(EXPLORE_PAUSE_MIN, EXPLORE_PAUSE_MAX) * FPS)
    player.pause_timer -= 1
    if player.pause_timer == 0:
        player.follow_offset = alliances.random_follow_offset()
    player.target = None


def showdown(player, players):
    """Endgame: with only a few players left, everyone knows where the others
    are and goes straight for the nearest one — no avoiding, no resting."""
    if player.retreat_timer > 0:
        player.retreat_timer -= 1  # a back-off from before the showdown still runs out
    others = [other for other in players if other is not player and other.alive]
    prey = nearest(player, others)
    if prey is None:
        player.target = None
        return
    player.prey = prey
    player.prey_last_seen = (prey.x, prey.y)
    player.hunt_timer = 0
    set_state(player, HUNTING)
    player.target = chase_target(player, prey)


def decide(player, arena, players):
    look_around(player, arena, players)
    player.state_timer += 1
    if player.hunt_cooldown > 0:
        player.hunt_cooldown -= 1

    # 0. Endgame showdown: the last few players hunt each other down
    if 1 < len(players) <= SHOWDOWN_PLAYERS:
        showdown(player, players)
        return

    # 1. Opening phase: rush or flee until done or time runs out
    if player.state == RUSH_LOOT and player.state_timer < RUSH_DURATION * FPS:
        wanted = [item for item in player.visible_loot if player.can_carry(item.kind)]
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

    is_member = player.alliance is not None and player.alliance.leader is not player

    # 2. Just fought and both survived: back away from the opponent.
    #    (Alliance members stay with their group instead.)
    if player.retreat_timer > 0:
        player.retreat_timer -= 1
        if not is_member:
            opponent = player.retreat_from
            set_state(player, AVOIDING)
            player.target = point_away_from(player, opponent.x, opponent.y)
            return

    # 3. Alliance members follow their leader instead of deciding for themselves
    if is_member:
        follow_leader(player)
        return

    # Players on their own use what they see; leaders use the whole group's view
    if player.alliance is not None:
        visible_loot, visible_players, known_loot = shared_view(player)
        members = player.alliance.members
    else:
        visible_loot, visible_players = player.visible_loot, player.visible_players
        known_loot = player.known_loot
        members = [player]

    need = most_urgent_need(members, player.state == RESTING)
    asleep = player.state == RESTING and need == "sleep"
    if need != "sleep":
        player.rest_spot = None  # not tired (any more): forget the sleeping spot

    # 4. Players in sight are allied with, fought or avoided
    #    (a sleeping player sees nothing)
    if not asleep and react_to_players(player, visible_players, need):
        return

    # 5. Urgent needs
    if need == "sleep":
        if player.state != RESTING:
            # Walk to a quiet spot by a wall first, then lie down there
            if player.rest_spot is None:
                player.rest_spot = shelter_spot(player)
            if distance(player.x, player.y, *player.rest_spot) > ARRIVE_DISTANCE:
                set_state(player, SHELTERING)
                player.target = player.rest_spot
                return
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
        remembered = [item for item in known_loot if item.kind == need]
        if remembered:
            # Head for the closest remembered item (it may already be gone)
            item = nearest(player, remembered)
            player.target = (item.x, item.y)
        else:
            # Nothing known: search parts of the arena not visited yet
            if player.search_point is None or distance(
                    player.x, player.y, *player.search_point) < ARRIVE_DISTANCE:
                # (searching always looks nearby, whatever the roaming trait)
                player.search_point = choose_explore_point(player, "normal")
            player.target = player.search_point
        return

    # 6. Collect loot in sight that can still be carried
    wanted = [item for item in visible_loot if player.can_carry(item.kind)]
    if wanted:
        set_state(player, GATHERING)
        item = nearest(player, wanted)
        player.target = (item.x, item.y)
        return

    # 7. Aggressive players and alliances head toward players they can't see yet
    if track(player, players):
        return

    # 8. Nothing urgent: explore
    explore(player)
