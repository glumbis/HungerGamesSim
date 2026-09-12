# Window settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# Colors (R, G, B)
BACKGROUND_COLOR = (30, 30, 30)
PLAYER_COLOR = (220, 220, 220)

# Player settings
NUM_PLAYERS = 24
PLAYER_RADIUS = 4           # size of the dot drawn on screen
PLAYER_MIN_SPEED = 1.0      # pixels moved per frame, slowest player
PLAYER_MAX_SPEED = 3.0      # pixels moved per frame, fastest player
WANDER_TURN_RATE = 0.15     # max radians the heading can drift per frame

# Starting formation
START_CIRCLE_RADIUS = 150   # how spread out the starting circle is

# Needs (hunger, thirst, sleep)
NEED_MAX = 100              # every need starts full at this value
NEED_WARNING_THRESHOLD = 30 # warning dot appears below this value
# Roughly how many seconds each need takes to drop from full to 0.
# These are short on purpose so deaths are visible while testing.
NEED_SECONDS_TO_EMPTY = {
    "hunger": 75,
    "thirst": 60,
    "sleep": 90,
}
NEED_RATE_VARIATION = 0.25  # each player's rate is up to 25% faster/slower

# Warning dot colors, one per need
NEED_WARNING_COLORS = {
    "hunger": (230, 140, 40),   # orange
    "thirst": (60, 140, 230),   # blue
    "sleep": (170, 90, 220),    # purple
}
WARNING_DOT_RADIUS = 2
WARNING_DOT_SPACING = 5     # horizontal gap between warning dots
WARNING_DOT_OFFSET_Y = 4    # extra gap between player dot and warning dots

# Loot
LOOT_COUNTS = {             # how many of each item spawn at the start
    "food": 30,
    "water": 30,
    "weapon": 12,
}
LOOT_CENTER_FRACTION = 0.5  # share of each item type placed in the central cluster
LOOT_CENTER_SPREAD = 35     # typical distance (pixels) of cluster items from the center
LOOT_SIZE = 4               # side length of the square drawn for an item
LOOT_COLORS = {
    "food": (230, 140, 40),     # orange, same as the hunger warning
    "water": (60, 140, 230),    # blue, same as the thirst warning
    "weapon": (200, 60, 60),    # red
}
LOOT_RESTORES = {           # which need each consumable item refills
    "food": "hunger",
    "water": "thirst",
}
LOOT_RESTORE_AMOUNT = 50    # how much one item refills its need
LOOT_USE_THRESHOLD = 50     # a carried item is used once its need drops below this
CARRY_LIMITS = {            # the most of each item a player will carry
    "food": 3,
    "water": 3,
    "weapon": 1,
}

# AI
VISION_RADIUS = 80          # how far (pixels) a player can see
STEER_TURN_RATE = 0.2       # max radians per frame when turning toward a target
STEER_SNAP_DISTANCE = 30    # closer than this, face the target directly (prevents circling it)
ARRIVE_DISTANCE = 10        # how close counts as "arrived" at a search point
RUSH_DURATION = 6           # seconds aggressive players rush the center at the start
FLEE_DURATION = 5           # max seconds cautious players run outward at the start
FLEE_DISTANCE = 280         # how far from the center fleeing players aim for
FLEE_EDGE_MARGIN = 60       # flee points are kept at least this far from the walls
SEEK_THRESHOLD = 40         # hunger/thirst below this, with nothing carried -> go find some
REST_THRESHOLD = 35         # sleep below this -> rest
REST_UNTIL = 90             # a resting player gets up once sleep reaches this
REST_SECONDS_TO_FULL = 15   # seconds of rest to recover sleep from 0 to 100

# Movement style
EXPLORE_CELL_SIZE = 150     # the arena is split into cells this size; players explore unvisited ones
EXPLORE_PAUSE_MIN = 0.5     # seconds a player pauses to look around on reaching a point
EXPLORE_PAUSE_MAX = 2.0
SHELTER_WALL_MARGIN = 40    # tired players walk to a spot this far from the nearest wall to sleep
# Speed multiplier per state (any state not listed moves at 1.0). Urgent
# states are faster, so chases and escapes stand out from calm movement.
STATE_SPEED_MULTIPLIERS = {
    "HUNTING": 1.5,
    "AVOIDING": 1.5,
    "RUSH_LOOT": 1.3,
    "FLEE_OUTWARD": 1.3,
    "SEEKING": 1.2,
}
CHASE_LINE_COLOR = (130, 45, 45)  # faint line from a hunter to its prey

# Debug view (toggle with the D key)
VISION_CIRCLE_COLOR = (55, 55, 55)
LEGEND_TEXT_COLOR = (200, 200, 200)

# Combat
STRENGTH_MIN = 1            # weakest possible player
STRENGTH_MAX = 10           # strongest possible player
WEAPON_STRENGTH_BONUS = 5   # added to strength while carrying a weapon
COMBAT_RANGE = 10           # a hunter this close to its prey starts a fight
STALK_DISTANCE = 20         # hunters wait this far from prey that can't be attacked yet
OUTCOME_WEIGHTS = {         # relative chance of each kind of fight outcome
    "ELIMINATION": 0.6,     # loser is eliminated, unless it escapes (then drops items)
    "STANDOFF": 0.2,        # nobody hurt, both back off
    "MUTUAL_LOSS": 0.2,     # both drop an item and back off
}
ESCAPE_DROP_FRACTION = 0.5  # share of each item type an escaping loser drops
RETREAT_SECONDS = 3         # after a fight both survive, they back off (and can't fight) this long
RETREAT_DISTANCE = 150      # how far away a retreating/avoiding player aims
ITEM_DROP_SCATTER = 15      # dropped items land up to this many pixels away

ESCAPE_BONUS = 0.2          # added to a loser's escape chance (raise if fights are too deadly)
ESCAPE_MAX = 0.9            # escape chance never goes above this

# Hunting and avoiding
# On first seeing another player, a player chooses to fight or avoid it.
# The chance to fight equals its aggression (0-1), multiplied by
# WEAPON_FEAR_FACTOR if the other player is armed and it is not.
WEAPON_FEAR_FACTOR = 0.5
HUNT_GIVE_UP_SECONDS = 10   # a hunter gives up a chase after this long
HUNT_COOLDOWN_SECONDS = 5   # after giving up (or a fight), no hunting for this long

# Alliances
ALLIANCE_CHANCE = 0.6       # chance to ally = this x (1 - aggression) of each side
ALLIANCE_MAX_SIZE = 4       # most members an alliance can have
ALLY_STRENGTH_SHARE = 0.5   # share of a nearby ally's strength added in a fight
ALLY_SUPPORT_RANGE = 60     # allies this close help in a fight
ALLY_SHARE_RANGE = 40       # allies this close hand over food/water
FOLLOW_SPREAD = 16          # members stay within about this distance of their leader
FOLLOW_LEASH = 45           # members collect loot at most this far from their leader
BETRAYAL_CHANCE_PER_MINUTE = 0.3  # for a member with aggression 1 (scaled by aggression)
ALLIANCE_COLORS = [         # each new alliance takes the next color
    (255, 120, 120),
    (120, 230, 120),
    (120, 160, 255),
    (255, 220, 100),
    (240, 120, 240),
    (110, 230, 230),
    (255, 170, 90),
    (190, 150, 255),
]
LEADER_RING_COLOR = (255, 255, 255)

# Fight marker
FIGHT_FLASH_SECONDS = 0.5
FIGHT_FLASH_COLOR = (255, 60, 60)
FIGHT_FLASH_RADIUS = 14
