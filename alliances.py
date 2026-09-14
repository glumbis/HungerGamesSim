"""Alliances: groups of players who don't fight each other. Each alliance
has a leader who decides what the whole group does (see ai.py); the other
members loosely follow it."""
import random

import events
import narration
from config import (
    FPS, LOOT_RESTORES, LOOT_USE_THRESHOLD,
    ALLIANCE_CHANCE, ALLIANCE_MAX_SIZE, ALLIANCE_MERGE_CHANCE, SAME_DISTRICT_ALLIANCE_CHANCE,
    ALLY_SHARE_RANGE, FOLLOW_SPREAD,
    BETRAYAL_CHANCE_PER_MINUTE, ALLIANCE_COLORS, ALLIANCE_WILLINGNESS, SHOWDOWN_PLAYERS,
)
from utils import distance


def random_follow_offset():
    """A random (dx, dy) offset from the leader: the member's own spot."""
    return (random.uniform(-FOLLOW_SPREAD, FOLLOW_SPREAD),
            random.uniform(-FOLLOW_SPREAD, FOLLOW_SPREAD))


def forget_prey(player):
    player.prey = None
    player.prey_last_seen = None
    player.hunt_timer = 0


def willingness(player):
    """How willing a player is to team up (0-1). Killers and cowards have a
    fixed value (ALLIANCE_WILLINGNESS); for balanced players it is higher
    the less aggressive they are. .get(key, default) returns the default
    when the key is missing."""
    return ALLIANCE_WILLINGNESS.get(player.temperament, 1 - player.aggression)


def choose_style(first, second):
    """An alliance's fixed style comes from its two founders:
    - a killer among them -> "bloodthirsty" (always fights)
    - two cowards         -> "defensive" (always avoids, but defends its members)
    - anything else       -> "opportunist" (decides fight by fight)"""
    temperaments = {first.temperament, second.temperament}  # a set: duplicates collapse
    if "killer" in temperaments:
        return "bloodthirsty"
    if temperaments == {"coward"}:
        return "defensive"
    return "opportunist"


class Alliance:
    created = 0  # alliances created so far; used to give each its own color

    def __init__(self, first, second):
        self.members = []
        self.color = ALLIANCE_COLORS[Alliance.created % len(ALLIANCE_COLORS)]
        Alliance.created += 1
        self.leader = None
        self.style = choose_style(first, second)
        self.add(first)
        self.add(second)
        self.choose_new_leader()

    def add(self, player):
        # Nobody keeps hunting someone who is now an ally
        for member in self.members:
            if member.prey is player:
                forget_prey(member)
            if player.prey is member:
                forget_prey(player)
        self.members.append(player)
        player.alliance = self
        player.follow_offset = random_follow_offset()

    def remove(self, player):
        """Take a player out of the alliance. Players who were allies once
        will never ally with each other again."""
        self.members.remove(player)
        player.alliance = None
        forget_prey(player)  # a group hunt does not carry over
        for member in self.members:
            member.former_allies.add(player)
            player.former_allies.add(member)

    def choose_new_leader(self):
        """The strongest member leads."""
        self.leader = max(self.members, key=lambda member: member.fighting_strength())

    def names(self):
        """Member names as text, e.g. "Cato, Clove and Glimmer"."""
        names = [member.name for member in self.members]
        if len(names) <= 1:
            return "".join(names)
        # all but the last joined with commas, then "and" before the last
        return ", ".join(names[:-1]) + " and " + names[-1]


def try_to_ally(player, other, chance=None):
    """`player` (on its own, or an alliance leader) meets `other`, who is
    not an ally. Two loners may form a new alliance, or a loner may join the
    other's alliance. `chance` replaces the usual chance (used in the
    bloodbath). Returns True if they are now allies."""
    if player.loner or other.loner:
        return False  # "no alliance" trait: trusts nobody
    if player.alliance is not None and other.alliance is not None:
        return try_to_merge(player, other)
    if other in player.former_allies:
        return False  # no second chances
    if other in player.alliance_rolls:
        return False  # each pair of players gets one chance per game

    # `or` gives the first of the two that is not None
    group = player.alliance or other.alliance
    if group is not None and len(group.members) >= ALLIANCE_MAX_SIZE:
        return False

    # Remember that this pair has now had its chance (whatever the outcome)
    player.alliance_rolls.add(other)
    other.alliance_rolls.add(player)

    # An alliance answers through its leader
    other_side = other.alliance.leader if other.alliance else other
    chance_given = chance is not None  # a chance is only passed in during the bloodbath
    if chance is None:
        chance = ALLIANCE_CHANCE * willingness(player) * willingness(other_side)
    # Tributes from the same district very likely stick together: the two who
    # meet are district partners, or the newcomer's partner is in the group
    if group is None:
        same_district = player.district == other.district
    else:
        newcomer = other if group is player.alliance else player
        same_district = any(member.district == newcomer.district for member in group.members)
    if same_district:
        chance = SAME_DISTRICT_ALLIANCE_CHANCE
    if random.random() >= chance:
        return False

    if group is None:
        alliance = Alliance(player, other)
        events.counts["alliances formed"] += 1
        events.log(narration.alliance_formed(alliance, bloodbath=chance_given))
    else:
        newcomer = other if group is player.alliance else player
        group.add(newcomer)
        events.log(narration.pick(narration.ALLIANCE_JOINED,
                                  newcomer=newcomer.name, leader=group.leader.name))
    return True


def try_to_merge(player, other):
    """Two alliances meet: a small chance (ALLIANCE_MERGE_CHANCE) they join
    into one, if the result is not too big. The bigger alliance takes in the
    smaller one; the strongest member of the new group leads. Each pair of
    players still gets only one roll per game. Returns True if merged."""
    group, other_group = player.alliance, other.alliance
    if group is other_group or other in player.alliance_rolls:
        return False
    if len(group.members) + len(other_group.members) > ALLIANCE_MAX_SIZE:
        return False
    if any(member in player.former_allies for member in other_group.members):
        return False
    player.alliance_rolls.add(other)
    other.alliance_rolls.add(player)
    if random.random() >= ALLIANCE_MERGE_CHANCE:
        return False

    if len(other_group.members) > len(group.members):
        group, other_group = other_group, group  # `group` is now the bigger one
    for member in list(other_group.members):  # copy: the list is emptied as we go
        other_group.members.remove(member)
        group.add(member)
    group.choose_new_leader()
    events.log(narration.pick(narration.ALLIANCE_MERGED,
                              names=group.names(), leader=group.leader.name))
    return True


def share_supplies(players):
    """A member low on food/water with none of its own gets one item from
    an ally close by."""
    for player in players:
        if player.alliance is None:
            continue
        for kind, need in LOOT_RESTORES.items():
            if player.inventory[kind] > 0 or player.needs[need] >= LOOT_USE_THRESHOLD:
                continue
            for ally in player.alliance.members:
                if ally is not player and ally.inventory[kind] > 0 and \
                        distance(player.x, player.y, ally.x, ally.y) <= ALLY_SHARE_RANGE:
                    ally.inventory[kind] -= 1
                    player.inventory[kind] += 1
                    break  # one item is enough


def disband(alliance, reason):
    if alliance.members:
        events.log(narration.alliance_broke_up(alliance, reason))
    for member in list(alliance.members):  # copy: remove() changes the list
        alliance.remove(member)


def betray(player):
    """The player leaves its alliance and turns on the nearest former ally."""
    alliance = player.alliance
    alliance.remove(player)
    victim = min(alliance.members,
                 key=lambda member: distance(player.x, player.y, member.x, member.y))
    player.prey = victim
    player.prey_last_seen = (victim.x, victim.y)
    player.hunt_timer = 0
    events.counts["betrayals"] += 1
    events.log(narration.pick(narration.BETRAYAL, traitor=player.name, victim=victim.name))

    if len(alliance.members) < 2:
        disband(alliance, "betrayal")
    elif alliance.leader is player:
        alliance.choose_new_leader()
        events.log(narration.pick(narration.NEW_LEADER, leader=alliance.leader.name))


def update_alliances(players):
    """Call once per frame, after dead players have been removed."""
    # Finale: with only a few players left, every alliance breaks up
    if len(players) <= SHOWDOWN_PLAYERS:
        for alliance in {player.alliance for player in players if player.alliance is not None}:
            disband(alliance, "the finale has begun")
        return

    # Tidy up alliances that lost members. {... for ...} is a set
    # comprehension: it collects each alliance only once.
    for alliance in {player.alliance for player in players if player.alliance is not None}:
        alliance.members = [member for member in alliance.members if member.alive]
        if len(alliance.members) < 2:
            disband(alliance, "too few members left")
        elif not alliance.leader.alive:
            alliance.choose_new_leader()
            events.log(narration.pick(narration.NEW_LEADER, leader=alliance.leader.name))

    # Betrayal: a small chance every frame, higher for aggressive members
    for player in players:
        if player.alliance is None:
            continue
        chance = BETRAYAL_CHANCE_PER_MINUTE * player.aggression / (60 * FPS)
        if random.random() < chance:
            betray(player)

    # Only one player can win: if everyone left is in the same alliance, it breaks up
    first = players[0].alliance if players else None
    if len(players) >= 2 and first is not None and \
            all(player.alliance is first for player in players):
        disband(first, "only allies are left")
