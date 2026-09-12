# Window settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# Colors (R, G, B)
BACKGROUND_COLOR = (30, 30, 30)
PLAYER_COLOR = (220, 220, 220)

# Player settings
NUM_PLAYERS = 24
PLAYER_RADIUS = 6           # size of the dot drawn on screen
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
WARNING_DOT_SPACING = 6     # horizontal gap between warning dots
WARNING_DOT_OFFSET_Y = 5    # extra gap between player dot and warning dots