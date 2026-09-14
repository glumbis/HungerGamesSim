# Window settings (the window can also be resized while running)
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# World: the arena is much larger than the window; a camera shows part of it
WORLD_WIDTH = 2200
WORLD_HEIGHT = 1650

# Colors (R, G, B)
BACKGROUND_COLOR = (30, 30, 30)
PLAYER_COLOR = (220, 220, 220)

# Player settings
NUM_PLAYERS = 24
PLAYER_RADIUS = 3           # size of the dot drawn on screen
PLAYER_MIN_SPEED = 0.3      # pixels moved per frame, slowest player
PLAYER_MAX_SPEED = 0.75     # pixels moved per frame, fastest player
WANDER_TURN_RATE = 0.15     # max radians the heading can drift per frame

# Starting formation
START_CIRCLE_RADIUS = 130   # distance of the launch plates from the cornucopia

# Needs (hunger, thirst, sleep)
NEED_MAX = 100              # every need starts full at this value
NEED_WARNING_THRESHOLD = 30 # warning dot appears below this value
# Roughly how many seconds each need takes to drop from full to 0.
# These are short on purpose so deaths are visible while testing.
NEED_SECONDS_TO_EMPTY = {
    "hunger": 160,
    "thirst": 130,
    "sleep": 85,           # sleep runs out fastest, so players must rest regularly
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
    "food": 25,
    "water": 30,
    "weapon": 12,
}
LOOT_CENTER_FRACTION = {    # share of each item type piled at the cornucopia
    "food": 0.3,
    "water": 0.3,
    "weapon": 0.8,          # most weapons are at the cornucopia: worth fighting for
}
LOOT_CENTER_SPREAD = 30     # typical distance (pixels) of cornucopia loot from the horn's mouth
LOOT_SIZE = 3               # side length of the square drawn for an item
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
VISION_RADIUS = 90        # how far (pixels) a player can see
STEER_TURN_RATE = 0.2       # max radians per frame when turning toward a target
STEER_SNAP_DISTANCE = 30    # closer than this, face the target directly (prevents circling it)
ARRIVE_DISTANCE = 10        # how close counts as "arrived" at a search point
RUSH_DURATION = 11          # seconds aggressive players rush the center at the start (the bloodbath lasts at least this long)
BLOODBATH_END_QUIET_SECONDS = 0.5  # the bloodbath only ends once no fight has been going on for this long
CENTER_PULL = 0.15          # exploring/searching destinations are moved this share of the way toward the middle (not for edge dwellers)
RUSH_BIAS = 0.25          # added to a balanced player's chance (its aggression) to rush the cornucopia
FLEE_DURATION = 8           # max seconds cautious players run outward at the start (nobody fights or allies with them meanwhile)
FLEE_DISTANCE = 550        # how far from the center fleeing players aim for
FLEE_EDGE_MARGIN = 60       # flee points are kept at least this far from the walls
SEEK_THRESHOLD = 40         # hunger/thirst below this, with nothing carried -> go find some
REST_THRESHOLD = 50         # sleep below this -> rest
SLEEP_COLLAPSE_THRESHOLD = 20  # sleep below this -> sleep on the spot, whatever else is going on
REST_UNTIL = 90             # a resting player gets up once sleep reaches this
REST_SECONDS_TO_FULL = 15   # seconds of rest to recover sleep from 0 to 100

# Movement style
EXPLORE_CELL_SIZE = 300     # the arena is split into cells this size; players explore unvisited ones
EXPLORE_PAUSE_MIN = 0.5     # seconds a player pauses to look around on reaching a point
EXPLORE_PAUSE_MAX = 2.0
SHELTER_WALL_MARGIN = 40    # tired players walk to a spot this far from the nearest wall to sleep
SHELTER_MAX_DISTANCE = 300  # ...but walk at most this far toward it before lying down
# Speed multiplier per state (any state not listed moves at 1.0). Urgent
# states are faster, so chases and escapes stand out from calm movement.
STATE_SPEED_MULTIPLIERS = {
    "HUNTING": 1.65,        # a little faster than AVOIDING, so chasers gain on their prey
    "AVOIDING": 1.5,
    "RUSH_LOOT": 1.1,       # kept low so the start isn't a frantic blur
    "FLEE_OUTWARD": 1.1,
    "SEEKING": 1.2,
    "TRACKING": 1.2,
    "INVESTIGATING": 1.2,
}
CHASE_LINE_COLOR = (130, 45, 45)  # faint line from a hunter to its prey

# Event feed (bottom-left corner)
FEED_MAX_LINES = 6          # most events shown at once
FEED_SECONDS = 10           # how long an event stays on screen
FEED_LINE_HEIGHT = 18
FEED_TEXT_COLOR = (235, 235, 235)
FEED_SHADOW_COLOR = (0, 0, 0)

# Personality traits (fixed for the whole game)
TEMPERAMENT_WEIGHTS = {     # share of players with each temperament
    "killer": 0.20,         # always rushes, always fights, tracks unseen players
    "balanced": 0.55,       # decides fight by fight, based on aggression
    "coward": 0.25,         # always flees at the start, always avoids
}
AGGRESSION_RANGES = {       # aggression (0-1) is drawn from the temperament's range
    "killer": (0.8, 1.0),
    "balanced": (0.2, 0.8),
    "coward": (0.0, 0.2),
}
ROAMING_WEIGHTS = {         # share of players with each roaming style
    "edge": 0.25,           # flees to the wall at the start, explores along the walls
    "normal": 0.50,         # explores nearby unvisited areas
    "explorer": 0.25,       # crosses the arena to far unvisited areas, short pauses
}
EXPLORER_PAUSE_FACTOR = 0.4 # explorers pause this fraction of the normal time
EXPLORE_MIN_TRIP = 500      # exploring players pick destinations at least this far away...
EXPLORER_MIN_TRIP = 850   # ...and explorers even further, so they head one way for a long time
EDGE_BAND = (25, 70)        # edge dwellers explore points this far (min, max) from the nearest wall
ALLIANCE_WILLINGNESS = {    # fixed willingness to ally (0-1); balanced players use 1 - aggression
    "killer": 0.3,
    "coward": 1.0,
}

# Endgame
SHOWDOWN_PLAYERS = 6        # with this many players left, the finale begins: all head to the cornucopia to fight to the death
FINALE_RADIUS = 250         # in the finale, players attack anyone this close to the cornucopia

# Simulation speed (Up/Down keys)
SPEED_LEVELS = [0.25, 0.5, 1, 2, 4, 8]  # simulation steps per drawn frame
HUD_TEXT_COLOR = (200, 200, 200)
WIN_BANNER_SECONDS = 4      # the winner's name is shown this long before the debrief

# Cornucopia and the start
COUNTDOWN_SECONDS = 3       # players wait on their launch plates this long
BLOODBATH_RADIUS = 80       # rushers start fighting (or backing off) this close to the cornucopia
# The bloodbath (these only apply to fights and alliances during the opening)
BLOODBATH_OUTCOME_WEIGHTS = {
    "ELIMINATION": 1.0,
    "STANDOFF": 0.0,
    "MUTUAL_LOSS": 0.0,
}
BLOODBATH_ESCAPE_FACTOR = 0.15  # a loser's usual escape chance is multiplied by this
BLOODBATH_ALLIANCE_CHANCE = 0.17# chance two lone rushers next to each other form a new alliance...
BLOODBATH_JOIN_CHANCE = 0.7     # ...but a rusher joins an existing alliance much more readily (fewer, bigger groups)
CORNUCOPIA_SIZE = 70        # size of the golden horn (world pixels)
CORNUCOPIA_COLOR = (205, 165, 70)
CORNUCOPIA_OUTLINE_COLOR = (110, 80, 25)
PLATE_RADIUS = 7
PLATE_COLOR = (72, 72, 72)
COUNTDOWN_TEXT_COLOR = (255, 230, 150)

# Camera
CAMERA_MAX_ZOOM = 3.0       # most zoomed in (screen pixels per world pixel)
CAMERA_OPENING_ZOOM = 2.2   # zoom on the cornucopia during the start
CAMERA_CHASE_ZOOM = 1.8     # most zoomed in when the automatic camera frames a chase or the players
CAMERA_FIGHT_ZOOM = 2.4     # zoom while the automatic camera watches a fight in progress
CAMERA_FIGHT_LINGER_SECONDS = 0.5  # the camera stays on a fight's spot this long after it ends
CAMERA_SMOOTHING = 0.08     # how quickly the automatic camera glides (share of the gap per frame)
CAMERA_PAN_SPEED = 12       # screen pixels per frame when panning with W/A/S/D
CAMERA_ZOOM_STEP = 1.15     # zoom factor per mouse wheel notch

# Minimap (bottom-right corner)
MINIMAP_WIDTH = 200
MINIMAP_BACKGROUND = (20, 26, 20)
MINIMAP_BORDER = (160, 160, 160)

# Terrain: large colored areas that affect gameplay (see "What terrain does" below)
TERRAIN_COLORS = {
    "meadow": (62, 84, 48),
    "forest": (34, 62, 38),
    "rock": (84, 82, 76),
    "sand": (128, 114, 76),
    "marsh": (48, 70, 68),
}
TERRAIN_WEIGHTS = {         # how common each terrain type is
    "meadow": 3,
    "forest": 3,
    "rock": 1.5,
    "sand": 1.2,
    "marsh": 1,
}
TERRAIN_ZONES = 22          # number of terrain areas
TERRAIN_WARP = 70           # how wavy the borders between areas are (world pixels)
# What terrain does
TERRAIN_VISIBILITY = {      # how far players see; forest wins if either player is in it
    "forest": 0.5,          # forest hides: seeing distance halved
    "sand": 1.3,            # open ground: seeing distance +30%
}
TERRAIN_SPEED = {           # movement speed factor
    "marsh": 0.6,
}
SAND_THIRST_FACTOR = 1.5    # thirst drops this much faster on sand
MARSH_REFILL_SECONDS = 40   # standing in marsh refills thirst from 0 to full in this time
MARSH_DRINK_UNTIL = 90      # a player drinking in marsh stays until thirst reaches this
MARSH_SEARCH_RADIUS = 600  # thirsty players look for marsh this far away
FOREST_SHELTER_RADIUS = 300 # tired players look for forest to sleep in this far away (cowards: twice as far)
TERRAIN_CLEAR_RADIUS = 260  # a meadow clearing surrounds the cornucopia
OUTSIDE_COLOR = (12, 12, 12)   # beyond the arena border
BORDER_COLOR = (95, 95, 85)

# Names
DEFAULT_NAMES = [           # in player order: District 1 boy, District 1 girl, District 2 boy, ...
    "D1 Boy", "Glimmer",    # Tributes named in the first book keep their names;
    "Cato", "Clove",        # the others are unnamed there and get a district label.
    "D3 Boy", "D3 Girl",
    "D4 Boy", "D4 Girl",
    "D5 Boy", "Foxface",
    "D6 Boy", "D6 Girl",
    "D7 Boy", "D7 Girl",
    "D8 Boy", "D8 Girl",
    "D9 Boy", "D9 Girl",
    "D10 Boy", "D10 Girl",
    "Thresh", "Rue",
    "Peeta", "Katniss",
]
NAME_MAX_LENGTH = 14
NAME_MIN_ZOOM = 0.7         # names above heads are hidden when zoomed out further than this
NAME_TEXT_COLOR = (235, 235, 235)

# Start screen
START_BACKGROUND = (22, 26, 22)
START_TITLE_COLOR = (235, 200, 110)
START_FIELD_COLOR = (48, 54, 46)
START_FIELD_ACTIVE_COLOR = (92, 102, 76)
START_BUTTON_COLOR = (190, 150, 60)

# Debug view (toggle with the D key)
VISION_CIRCLE_COLOR = (55, 55, 55)
LEGEND_TEXT_COLOR = (200, 200, 200)

# Combat
STRENGTH_MIN = 1            # weakest possible player
STRENGTH_MAX = 10           # strongest possible player
WEAPON_STRENGTH_BONUS = 5   # added to strength while carrying a weapon
COMBAT_RANGE = 10           # a hunter this close to its prey starts a fight
STALK_DISTANCE = 20         # hunters wait this far from prey that can't be attacked yet
FIGHT_DURATION_MIN = 1.0    # a fight lasts between these many seconds; the two
FIGHT_DURATION_MAX = 3.0    # fighters stand still until it is decided
FIGHT_RING_COLOR = (255, 110, 60)  # pulsing ring around a fight in progress
FIGHT_ALERT_RADIUS = 300    # players this close hear a fight start
ALERT_SECONDS = 8           # how long a player remembers where it heard a fight
INVESTIGATE_MIN_FIGHT_CHANCE = 0.7  # only players at least this likely to fight go toward a fight they hear
LULL_SECONDS = 45           # no fight for this long: aggressive players are told where others are
TIP_SECONDS = 25            # ...and head for that player for at most this long

# Stamina: sprinting (hunting, avoiding, ...) tires players out
SPRINT_SECONDS = 4          # full stamina lasts this long while sprinting; then no more sprinting
STAMINA_RECOVERY_SECONDS = 8  # time to recover from empty to full while not sprinting
TIRED_ESCAPE_FACTOR = 0.3   # an exhausted loser's escape chance is multiplied by this
OUTCOME_WEIGHTS = {         # relative chance of each kind of fight outcome
    "ELIMINATION": 0.85,    # loser is eliminated, unless it escapes (then drops items)
    "STANDOFF": 0.05,       # nobody hurt, both back off
    "MUTUAL_LOSS": 0.10,    # both drop an item and back off
}
ESCAPE_DROP_FRACTION = 0.5  # share of each item type an escaping loser drops
RETREAT_SECONDS = 3         # after a fight both survive, they back off (and can't fight) this long
RETREAT_DISTANCE = 150      # how far away a retreating/avoiding player aims
ITEM_DROP_SCATTER = 15      # dropped items land up to this many pixels away

ESCAPE_BONUS = -0.20        # added to a loser's escape chance (raise if fights are too deadly)
ESCAPE_MAX = 0.9            # escape chance never goes above this

# Hunting and avoiding
# On first seeing another player, a player chooses to fight or avoid it.
# The chance to fight equals its aggression (0-1), multiplied by
# WEAPON_FEAR_FACTOR if the other player is armed and it is not.
WEAPON_FEAR_FACTOR = 0.5
HUNT_GIVE_UP_SECONDS = 6    # a hunter gives up a chase after this long
AVOID_COMMIT_SECONDS = 2.0  # a player backing away keeps going this long (stops jiggling at the edge of sight)
HUNT_COOLDOWN_SECONDS = 5   # after giving up (or a fight), no hunting for this long

# Alliances
ALLIANCE_CHANCE = 0.5      # chance to ally = this x (1 - aggression) of each side
LONERS_PER_GAME = (2, 6)    # this many players (random, inclusive) never join any alliance
ALLIANCE_MAX_SIZE = 6      # most members an alliance can have
ALLY_STRENGTH_SHARE = 0.8   # share of a nearby ally's strength added in a fight
ALLY_SUPPORT_RANGE = 80     # allies this close help in a fight
ALLY_SHARE_RANGE = 40       # allies this close hand over food/water
FOLLOW_SPREAD = 16          # members stay within about this distance of their leader
FOLLOW_LEASH = 45           # members collect loot at most this far from their leader
BETRAYAL_CHANCE_PER_MINUTE = 0.3  # for a member with aggression 1 (scaled by aggression)
ALLIANCE_AGGRESSION_BONUS = 0.2   # added to a group's chance to fight for each extra member
ALLIANCE_SENSE_RADIUS = 115# alliance members notice non-allies this far away (loners: VISION_RADIUS)
ALLIANCE_RETREAT_SECONDS = 1  # alliances back off only this long after a fight (loners: RETREAT_SECONDS)
SAME_DISTRICT_ALLIANCE_CHANCE = 0.9  # chance to ally with a player from your own district (replaces the usual chance)
ALLIANCE_MERGE_CHANCE = 0.15 # chance two alliances meeting face to face merge (if the result fits ALLIANCE_MAX_SIZE)
CAMP_ALLIANCE_SIZE = 4      # alliances at least this big stay around the cornucopia...
CAMP_RADIUS = 350           # ...exploring only within this distance of it
# Chases: a hunter that has chased its prey for a while has the upper hand
CHASE_MIN_SECONDS = 1.0     # a fight counts as the end of a chase after chasing this long
CHASER_STRENGTH_FACTOR = 1.3  # the chaser's strength is multiplied by this in that fight
CHASED_ESCAPE_FACTOR = 0.6  # and the chased player's escape chance by this
# Tracking: an aggressive alliance heads roughly toward players it can't see yet
TRACK_RADIUS = 300          # how far away such players can be
TRACK_MIN_FIGHT_CHANCE = 0.8  # only groups at least this likely to fight go tracking
TRACK_STEP = 120            # each estimated waypoint lies this far ahead
TRACK_ANGLE_NOISE = 0.5     # max error (radians) in the estimated direction
TRACK_UPDATE_SECONDS = 2    # the direction is re-estimated this often
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
