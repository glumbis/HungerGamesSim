"""Fights between players. A fight starts when a hunter reaches its prey.
The result is random, but weighted: strength decides who comes out on top,
speed decides whether a loser manages to escape."""
import math
import random

from config import (
    FPS, COMBAT_RANGE, OUTCOME_WEIGHTS, ALLY_STRENGTH_SHARE, ALLY_SUPPORT_RANGE,
    ESCAPE_DROP_FRACTION, RETREAT_SECONDS, ESCAPE_BONUS, ESCAPE_MAX,
)
from ai import stop_hunting, RESTING
from utils import distance

# Outcome names (must match the keys of OUTCOME_WEIGHTS in config.py)
ELIMINATION = "ELIMINATION"
STANDOFF = "STANDOFF"
MUTUAL_LOSS = "MUTUAL_LOSS"


def effective_strength(player):
    """Strength used in a fight: the player's own strength (including any
    weapon), plus a share of the strength of awake allies close enough to help."""
    total = player.fighting_strength()
    if player.alliance is not None:
        for ally in player.alliance.members:
            if ally is not player and ally.alive and ally.state != RESTING and \
                    distance(player.x, player.y, ally.x, ally.y) <= ALLY_SUPPORT_RANGE:
                total += ALLY_STRENGTH_SHARE * ally.fighting_strength()
    return total


def handle_fights(players, arena):
    """Start a fight wherever a hunter has reached its prey."""
    for attacker in players:
        defender = attacker.prey
        if defender is None or not attacker.alive or not defender.alive:
            continue
        if attacker.retreat_timer > 0 or defender.retreat_timer > 0:
            continue  # one of them has only just fought
        if distance(attacker.x, attacker.y, defender.x, defender.y) <= COMBAT_RANGE:
            fight(attacker, defender, arena)


def fight(attacker, defender, arena):
    strength_a = effective_strength(attacker)
    strength_d = effective_strength(defender)
    arena.add_flash((attacker.x + defender.x) / 2, (attacker.y + defender.y) / 2)

    # Who comes out on top: the chance is each side's share of the total strength
    if random.random() < strength_a / (strength_a + strength_d):
        winner, loser = attacker, defender
    else:
        winner, loser = defender, attacker

    # Which kind of outcome: random.choices picks one name, using the weights
    # (it returns a list, so [0] takes the single pick out of it)
    outcome = random.choices(
        list(OUTCOME_WEIGHTS), weights=list(OUTCOME_WEIGHTS.values())
    )[0]

    summary = (f"Fight: Player {attacker.id} (str {strength_a:.1f}) attacked "
               f"Player {defender.id} (str {strength_d:.1f}) -> ")

    if outcome == ELIMINATION:
        # The loser may still escape; the faster it is compared to the
        # winner, the better its chance
        escape_chance = loser.speed / (loser.speed + winner.speed) + ESCAPE_BONUS
        escape_chance = min(escape_chance, ESCAPE_MAX)
        if random.random() < escape_chance:
            drop_items(loser, arena, ESCAPE_DROP_FRACTION)
            retreat(winner, loser)
            retreat(loser, winner)
            print(summary + f"Player {loser.id} lost but escaped, dropping supplies.")
        else:
            loser.alive = False
            loser.cause_of_death = "combat"
            loser.killer_id = winner.id
            winner.kills += 1
            drop_items(loser, arena, 1.0)  # everything it carried
            stop_hunting(winner)
            print(summary + f"Player {winner.id} eliminated Player {loser.id}.")
    elif outcome == STANDOFF:
        retreat(attacker, defender)
        retreat(defender, attacker)
        print(summary + "standoff, both backed off.")
    else:  # MUTUAL_LOSS
        drop_random_item(attacker, arena)
        drop_random_item(defender, arena)
        retreat(attacker, defender)
        retreat(defender, attacker)
        print(summary + "both hurt, each dropped an item and backed off.")


def retreat(player, opponent):
    """Make a player back away from its opponent for a while. It can't
    fight during this time, and won't start hunting again straight away."""
    player.retreat_timer = RETREAT_SECONDS * FPS
    player.retreat_from = opponent
    stop_hunting(player, cooldown=True)


def drop_items(player, arena, fraction):
    """Drop a share of each carried item type on the ground. math.ceil
    rounds up, so a player carrying any of a type drops at least one."""
    for kind, count in player.inventory.items():
        amount = math.ceil(count * fraction)
        for _ in range(amount):
            arena.drop_item(kind, player.x, player.y, dropped_by=player)
        player.inventory[kind] -= amount


def drop_random_item(player, arena):
    """Drop one randomly chosen carried item, if the player has any."""
    carried = [kind for kind, count in player.inventory.items() if count > 0]
    if carried:
        kind = random.choice(carried)
        arena.drop_item(kind, player.x, player.y, dropped_by=player)
        player.inventory[kind] -= 1
