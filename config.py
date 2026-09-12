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
VISION_RADIUS = 120         # how far (pixels) a player can see
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

# Debug view (toggle with the D key)
VISION_CIRCLE_COLOR = (55, 55, 55)
LEGEND_TEXT_COLOR = (200, 200, 200)
