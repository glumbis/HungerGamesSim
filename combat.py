"""Fights between players. A fight starts when a hunter reaches its prey.
The two fighters are locked in place for a few seconds, then the result is
decided: strength decides who comes out on top; speed and stamina decide
whether a loser manages to escape. A fight makes noise that nearby players
hear (see ai.respond_to_noise)."""
import math
import random

from config import (
    FPS, COMBAT_RANGE, OUTCOME_WEIGHTS, ALLY_STRENGTH_SHARE, ALLY_SUPPORT_RANGE,
    ESCAPE_DROP_FRACTION, RETREAT_SECONDS, ESCAPE_BONUS, ESCAPE_MAX,
    ALLIANCE_RETREAT_SECONDS, SHOWDOWN_PLAYERS,
    FIGHT_DURATION_MIN, FIGHT_DURATION_MAX, FIGHT_ALERT_RADIUS, ALERT_SECONDS,
    TIRED_ESCAPE_FACTOR,
)
from ai import stop_hunting, set_state, RESTING, FIGHTING
from utils import distance

# Outcome names (must match the keys of OUTCOME_WEIGHTS in config.py)
ELIMINATION = "ELIMINATION"
STANDOFF = "STANDOFF"
MUTUAL_LOSS = "MUTUAL_LOSS"


class Fight:
    """A fight in progress between two players."""

    def __init__(self, attacker, defender, to_the_death):
        self.attacker = attacker
        self.defender = defender
        self.to_the_death = to_the_death  # True in the finale
        self.x = (attacker.x + defender.x) / 2  # where the fight is happening
        self.y = (attacker.y + defender.y) / 2
        self.frames_left = int(random.uniform(FIGHT_DURATION_MIN, FIGHT_DURATION_MAX) * FPS)


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
    """Every frame: start a fight wherever a hunter has reached its prey, and
    decide the fights whose time is up."""
    finale = len(players) <= SHOWDOWN_PLAYERS  # endgame: fights are to the death
    for attacker in players:
        defender = attacker.prey
        if defender is None or not attacker.alive or not defender.alive:
            continue
        if attacker.fight is not None or defender.fight is not None:
            continue  # one of them is already fighting
        if attacker.retreat_timer > 0 or defender.retreat_timer > 0:
            continue  # one of them has only just fought
        if distance(attacker.x, attacker.y, defender.x, defender.y) <= COMBAT_RANGE:
            start_fight(attacker, defender, arena, players, finale)

    # Count down the fights in progress. We loop over a copy (list(...))
    # because finished fights are removed from arena.fights.
    for fight in list(arena.fights):
        fight.frames_left -= 1
        if not fight.attacker.alive or not fight.defender.alive:
            end_fight(fight, arena)  # someone died of hunger, thirst or sleep mid-fight
        elif fight.frames_left <= 0:
            end_fight(fight, arena)
            resolve_fight(fight.attacker, fight.defender, arena, fight.to_the_death)


def start_fight(attacker, defender, arena, players, to_the_death):
    fight = Fight(attacker, defender, to_the_death)
    arena.fights.append(fight)
    for fighter in (attacker, defender):
        fighter.fight = fight
        set_state(fighter, FIGHTING)
        fighter.target = None  # locked in place until the fight is decided

    # The noise carries: everyone else nearby hears where the fight is
    for player in players:
        if player is attacker or player is defender or not player.alive:
            continue
        if distance(player.x, player.y, fight.x, fight.y) <= FIGHT_ALERT_RADIUS:
            player.heard_fight = (fight.x, fight.y)
            player.heard_timer = ALERT_SECONDS * FPS


def end_fight(fight, arena):
    arena.fights.remove(fight)
    fight.attacker.fight = None
    fight.defender.fight = None


def resolve_fight(attacker, defender, arena, to_the_death):
    """Decide how a finished fight turned out."""
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
    if to_the_death:
        outcome = ELIMINATION  # in the finale every fight is to the death

    summary = (f"Fight: {attacker.name} (str {strength_a:.1f}) attacked "
               f"{defender.name} (str {strength_d:.1f}) -> ")

    if outcome == ELIMINATION:
        # The loser may still escape: the faster it is compared to the winner,
        # the better its chance, and a tired loser (after a long chase) has
        # much less chance. max(0.0, ...) stops the chance going below zero.
        escape_chance = loser.speed / (loser.speed + winner.speed) + ESCAPE_BONUS
        escape_chance = max(0.0, min(escape_chance, ESCAPE_MAX))
        escape_chance *= TIRED_ESCAPE_FACTOR + (1 - TIRED_ESCAPE_FACTOR) * loser.stamina
        if to_the_death:
            escape_chance = 0  # ...and in the finale nobody escapes
        if random.random() < escape_chance:
            drop_items(loser, arena, ESCAPE_DROP_FRACTION)
            retreat(winner, loser)
            retreat(loser, winner)
            print(summary + f"{loser.name} lost but escaped, dropping supplies.")
        else:
            loser.alive = False
            loser.cause_of_death = "combat"
            loser.killer_id = winner.id
            loser.killer_name = winner.name
            winner.kills += 1
            drop_items(loser, arena, 1.0)  # everything it carried
            stop_hunting(winner)
            print(summary + f"{winner.name} eliminated {loser.name}.")
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
    """Make a player back off from its opponent for a while; it can't fight
    during this time.
    - A player on its own also won't start a new hunt straight away.
    - In an alliance the whole group backs off together (members follow
      their leader), and then goes after the opponent: the leader keeps it
      as prey, and resumes the chase once the back-off is over."""
    player.retreat_from = opponent
    if player.alliance is None:
        player.retreat_timer = RETREAT_SECONDS * FPS
        stop_hunting(player, cooldown=True)
        return

    # Alliances back off only briefly, then strike again
    player.retreat_timer = ALLIANCE_RETREAT_SECONDS * FPS
    stop_hunting(player)
    leader = player.alliance.leader
    leader.retreat_timer = max(leader.retreat_timer, ALLIANCE_RETREAT_SECONDS * FPS)
    leader.retreat_from = opponent
    leader.prey = opponent
    leader.prey_last_seen = (opponent.x, opponent.y)
    leader.hunt_timer = 0


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
