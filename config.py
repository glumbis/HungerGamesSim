"""Every number and color the simulation uses, grouped by topic. Change a
value here to tune the Games; nothing else needs editing."""

# =============================================================================
# Window, world and speed
# =============================================================================
SCREEN_WIDTH = 1000         # starting window size (the window can be resized)
SCREEN_HEIGHT = 700
FPS = 60                    # simulation steps per second at normal speed
SPEED_LEVELS = [0.25, 0.5, 1, 2, 4, 8]  # Up/Down keys: simulation steps per drawn frame

WORLD_WIDTH = 2200          # the arena; the camera shows part of it
WORLD_HEIGHT = 1650

# =============================================================================
# Tributes
# =============================================================================
NUM_PLAYERS = 24
PLAYER_RADIUS = 3           # size of a dot (world pixels)
PLAYER_MIN_SPEED = 0.18     # pixels moved per frame, slowest tribute
PLAYER_MAX_SPEED = 0.45     # pixels moved per frame, fastest tribute
STRENGTH_MIN = 1
STRENGTH_MAX = 10
WANDER_TURN_RATE = 0.15     # max random drift of the heading per frame (radians)
STEER_TURN_RATE = 0.2       # max turn per frame toward a target (radians)
STEER_SNAP_DISTANCE = 30    # closer than this, face the target directly (prevents circling it)
ARRIVE_DISTANCE = 10        # this close counts as "arrived"

# Names (in player order: District 1 boy, District 1 girl, District 2 boy, ...).
# Tributes named in the first book keep their names; the rest get a district label.
DEFAULT_NAMES = [
    "D1 Boy", "Glimmer",
    "Cato", "Clove",
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

# Personality (fixed for the whole Games; can also be chosen on the start screen)
TEMPERAMENT_WEIGHTS = {     # share of tributes with each temperament
    "killer": 0.20,         # always rushes, always fights, tracks unseen tributes
    "balanced": 0.55,       # decides fight by fight, based on aggression
    "coward": 0.25,         # always flees at the start, always avoids
}
AGGRESSION_RANGES = {       # aggression (0-1) is drawn from the temperament's range
    "killer": (0.8, 1.0),
    "balanced": (0.2, 0.8),
    "coward": (0.0, 0.2),
}
ROAMING_WEIGHTS = {         # share of tributes with each roaming style
    "edge": 0.25,           # flees to the wall at the start, explores along the walls
    "normal": 0.50,         # explores nearby unvisited areas
    "explorer": 0.25,       # crosses the arena to far unvisited areas, short pauses
}
LONERS_PER_GAME = (2, 6)    # this many random tributes never join any alliance

# Proficiency: every tribute is especially good at one thing
PROFICIENCIES = ["knife", "spear", "axe", "sword", "bow", "fists", "survival", "stealth", "speed", "tracking"]
PROFICIENCY_DESCRIPTIONS = {
    "knife": "knife fighter", "spear": "spear fighter", "axe": "axe fighter", "sword": "swordfighter",
    "bow": "archer", "fists": "brawler", "survival": "survivalist", "stealth": "stealthy",
    "speed": "fast runner", "tracking": "tracker",
}
PROFICIENT_WEAPON_FACTOR = 1.6  # strength while holding the weapon it is proficient in
FISTS_BONUS = 4             # extra strength without a weapon for brawlers
SURVIVAL_NEED_FACTOR = 0.75 # survivalists' hunger and thirst drop this much slower
STEALTH_VISIBILITY = 0.7    # stealthy tributes are only seen this far (share of normal)
SPEED_PROFICIENCY_FACTOR = 1.2  # fast runners move this much faster (and escape ×1.3)
TRACKING_FACTOR = 2.0       # trackers sense unseen tributes this much further (and chase ×1.5 longer)

# District skills (one per district that has one)
DISTRICT_SKILLS = {
    1: "luxury",   # sponsors love them: more gifts
    2: "training", # trained Careers: +2 strength
    3: "traps",    # ambushes more often
    4: "fishing",  # hunger also refills in marsh
    5: "cunning",  # escapes more often
    7: "axes",     # extra strength with an axe
    11: "farming", # sometimes forages food in forest and meadow
    12: "archery", # extra strength with a bow
}
SKILL_DESCRIPTIONS = {
    "luxury": "sponsor favorite", "training": "trained fighter", "traps": "trap setter",
    "fishing": "fisher", "cunning": "hard to catch", "axes": "axe wielder",
    "farming": "forager", "archery": "archer",
}
FORAGE_CHANCE = 0.0015      # per frame, for farming tributes in forest or meadow

# =============================================================================
# Needs: hunger, thirst and sleep (a tribute dies when one reaches 0)
# =============================================================================
NEED_MAX = 100
NEED_SECONDS_TO_EMPTY = {   # roughly how long each need takes to drop from full to 0
    "hunger": 165,
    "thirst": 130,
    "sleep": 135,
}
NEED_RATE_VARIATION = 0.25  # each tribute's rates are up to 25% faster or slower
NEED_WARNING_THRESHOLD = 30 # a warning dot appears above the tribute below this
SEEK_THRESHOLD = 40         # hunger/thirst below this, with nothing carried: go and find some

REST_THRESHOLD = 50         # sleep below this: find a spot and rest
REST_UNTIL = 90             # a resting tribute gets up once sleep reaches this
REST_SECONDS_TO_FULL = 15   # seconds of rest to recover sleep from 0 to 100
MIN_SLEEP_SECONDS = 8       # once asleep, a tribute sleeps at least this long (unless attacked or in danger)
SLEEP_COLLAPSE_THRESHOLD = 20  # sleep below this: sleep on the spot (once not hunting or escaping)
SHELTER_WALL_MARGIN = 40    # without forest nearby, tired tributes sleep this far from the nearest wall...
SHELTER_MAX_DISTANCE = 300  # ...but walk at most this far to get there
FOREST_SHELTER_RADIUS = 300 # tired tributes look for forest to sleep in this far away (cowards: twice as far)

# =============================================================================
# Loot
# =============================================================================
LOOT_COUNTS = {             # items spawned at the start (nothing respawns)
    "food": 14,
    "water": 16,
    "weapon": 12,
}
LOOT_CENTER_FRACTION = {    # share of each item type piled at the cornucopia
    "food": 0.3,
    "water": 0.3,
    "weapon": 0.8,          # most weapons are at the cornucopia: worth fighting for
}
LOOT_CENTER_SPREAD = 55     # typical distance of cornucopia loot from the horn's mouth
LOOT_RESTORES = {           # which need each consumable item refills
    "food": "hunger",
    "water": "thirst",
}
LOOT_RESTORE_AMOUNT = 40    # how much one item refills its need
LOOT_USE_THRESHOLD = 50     # a carried item is used once its need drops below this
CARRY_LIMITS = {"food": 3, "water": 3, "weapon": 1}
ITEM_DROP_SCATTER = 15      # items dropped in a fight land up to this far away

WEAPON_TYPES = {            # type -> (strength bonus, reach: how close it must get to attack)
    "knife": (3, 10),
    "spear": (5, 14),
    "axe": (6, 10),
    "sword": (6, 10),
    "bow": (4, 30),
}
WEAPON_STRENGTH_BONUS = 5   # bonus for a weapon of unknown type
SKILL_WEAPON_BONUS = 3      # extra strength for axes (District 7) and bows (District 12)

# =============================================================================
# The start: countdown, rush and bloodbath
# =============================================================================
COUNTDOWN_SECONDS = 3       # tributes wait on their launch plates this long
START_CIRCLE_RADIUS = 190   # distance of the launch plates from the cornucopia
RUSH_BIAS = 0.25            # added to a balanced tribute's chance (its aggression) to rush the cornucopia
RUSH_DURATION = 15          # rushers keep at it (and the bloodbath lasts) at least this long
FLEE_DURATION = 8           # max seconds cautious tributes run outward (nobody fights or allies with them meanwhile)
FLEE_DISTANCE = 800         # how far from the center fleeing tributes aim for
FLEE_EDGE_MARGIN = 60       # flee points are kept at least this far from the walls
BLOODBATH_RADIUS = 100      # rushers this close to each other fight, flee or team up
BLOODBATH_END_QUIET_SECONDS = 0.5  # the bloodbath only ends once no fight has been going on for this long
BLOODBATH_OUTCOME_WEIGHTS = {"ELIMINATION": 1.0, "STANDOFF": 0.0, "MUTUAL_LOSS": 0.0}
BLOODBATH_ESCAPE_FACTOR = 0.6   # a loser's usual escape chance is multiplied by this
BLOODBATH_ALLIANCE_CHANCE = 0.17  # chance two lone rushers next to each other form a new alliance...
BLOODBATH_JOIN_CHANCE = 0.7     # ...but joining an existing alliance is much likelier (fewer, bigger groups)
BIG_ALLIANCE_SIZE = 3       # with two or more alliances this big in the opening, the smallest leaves the middle...
LEAVE_DISTANCE = 650        # ...for a point this far from the cornucopia

# =============================================================================
# Moving around
# =============================================================================
VISION_RADIUS = 90          # how far a tribute sees
STATE_SPEED_MULTIPLIERS = { # urgent states move faster (states not listed: 1.0)
    "HUNTING": 1.65,        # a little faster than AVOIDING, so chasers gain on their prey
    "AVOIDING": 1.5,
    "RUSH_LOOT": 1.1,
    "FLEE_OUTWARD": 1.1,
    "SEEKING": 1.2,
    "TRACKING": 1.2,
    "INVESTIGATING": 1.2,
}
SPRINT_SECONDS = 4          # full stamina lasts this long while moving in a fast state...
STAMINA_RECOVERY_SECONDS = 8  # ...and refills from empty in this long otherwise

EXPLORE_CELL_SIZE = 300     # the arena is split into cells this size; tributes explore unvisited ones
EXPLORE_MIN_TRIP = 650      # exploring tributes pick destinations at least this far away...
EXPLORER_MIN_TRIP = 1000    # ...and explorers even further
EXPLORE_PAUSE_MIN = 0.5     # seconds a tribute pauses to look around on arriving
EXPLORE_PAUSE_MAX = 2.0
EXPLORER_PAUSE_FACTOR = 0.4 # explorers pause this share of the normal time
EDGE_BAND = (25, 70)        # edge dwellers explore points this far (min, max) from the nearest wall
CENTER_PULL = 0.04          # exploring destinations are moved this share of the way toward the middle (not edge dwellers)
CHILL_CHANCE = 0.5          # chance, on reaching a destination, to sit down for a while...
CHILL_START_PER_SECOND = 0.05  # ...and chance per second an idle tribute sits down anyway
CHILL_SECONDS = (6, 18)     # how long it stays put

# =============================================================================
# Meeting other tributes: fight or avoid
# =============================================================================
# On first seeing another tribute, a tribute chooses to fight or avoid it. The
# chance to fight is its aggression (plus alliance bonuses), multiplied by
# WEAPON_FEAR_FACTOR if the other is armed and it is not.
WEAPON_FEAR_FACTOR = 0.5
HUNT_GIVE_UP_SECONDS = 5    # a hunter gives up a chase after this long
HUNT_COOLDOWN_SECONDS = 5   # after giving up (or a fight), no new hunt for this long
AVOID_COMMIT_SECONDS = 2.0  # a tribute backing away keeps going this long (stops jiggling at the edge of sight)
RETREAT_SECONDS = 3         # after a fight both survive, they back off (and can't fight) this long
RETREAT_DISTANCE = 150      # how far away a retreating/avoiding tribute aims
STALK_DISTANCE = 20         # hunters wait this far from prey that can't be attacked yet
TRACK_RADIUS = 220          # the most aggressive tributes head for unseen tributes this close...
TRACK_MIN_FIGHT_CHANCE = 0.9  # ...if their fight chance is at least this
TRACK_STEP = 120            # each estimated waypoint lies this far ahead
TRACK_ANGLE_NOISE = 0.5     # max error (radians) in the estimated direction
TRACK_UPDATE_SECONDS = 2    # the direction is re-estimated this often
FIGHT_ALERT_RADIUS = 220    # tributes this close hear a fight start...
ALERT_SECONDS = 8           # ...and remember where for this long
INVESTIGATE_MIN_FIGHT_CHANCE = 0.8  # only tributes at least this likely to fight go and look

# Quiet spells: no fight for a while
LULL_SECONDS = 45           # no fight for this long: some random tributes and alliances head for the middle...
LULL_GATHER_SHARE = 0.4     # ...this share of the loners and alliance leaders (at least 2)...
TIP_SECONDS = 25            # ...for at most this long...
GATHER_RADIUS = 150         # ...until this close to the cornucopia...
LULL_FIGHT_BONUS = 0.15     # ...and until the next fight, tributes who usually avoid (fight chance < 0.5) get this added

# Hiding, ambushes, revenge and reputation
HIDE_CHANCE = 0.02          # chance per frame that a hunted, cautious loner in forest climbs a tree
HIDE_SECONDS = 10
HIDE_SPOT_DISTANCE = 12     # a hidden tribute can only be spotted this close
HIDE_MAX_AGGRESSION = 0.6
AMBUSH_CHANCE = 0.8         # chance per 10 idle seconds that a lone killer sets an ambush by water or supplies
AMBUSH_SECONDS = 20
AMBUSH_STRENGTH_FACTOR = 1.4  # an ambusher's strength in the fight that springs the ambush
REVENGE_CHANCE = 0.4        # chance a (non-coward) district partner swears revenge on the killer
REVENGE_RADIUS = 400        # it goes after the killer while this close
FEARED_KILLS = 3            # with this many kills a tribute is feared...
FEARED_FACTOR = 0.6         # ...others' chance to fight it is multiplied by this (killers: ×1.3)

# =============================================================================
# Fights
# =============================================================================
COMBAT_RANGE = 10           # an unarmed hunter this close to its prey starts a fight
FIGHT_DURATION_MIN = 1.5    # a fight lasts between these many seconds; the two
FIGHT_DURATION_MAX = 3.5    # fighters stand still until it is decided
OUTCOME_WEIGHTS = {         # relative chance of each kind of fight outcome
    "ELIMINATION": 0.80,    # the loser dies, unless it escapes (then drops items and is injured)
    "STANDOFF": 0.08,       # nobody hurt, both back off
    "MUTUAL_LOSS": 0.12,    # both drop an item, are injured and back off
}
ESCAPE_BONUS = -0.28        # added to a loser's escape chance (raise if fights are too deadly)
ESCAPE_MAX = 0.9            # escape chance never goes above this
TIRED_ESCAPE_FACTOR = 0.3   # an exhausted loser's escape chance is multiplied by this
ESCAPE_DROP_FRACTION = 0.5  # share of each item type an escaping loser drops
CHASE_MIN_SECONDS = 1.0     # a fight at the end of a chase this long...
CHASER_STRENGTH_FACTOR = 1.3  # ...multiplies the chaser's strength by this...
CHASED_ESCAPE_FACTOR = 0.6  # ...and the chased tribute's escape chance by this
INJURY_SECONDS = 30         # an injured tribute (escaped a fight or a mutt) is hurt this long...
INJURY_SPEED_FACTOR = 0.7   # ...moving slower...
INJURY_STRENGTH_FACTOR = 0.7  # ...and fighting weaker

# =============================================================================
# Alliances
# =============================================================================
ALLIANCE_CHANCE = 0.5       # chance to ally = this × willingness of each side
ALLIANCE_WILLINGNESS = {    # fixed willingness (0-1); balanced tributes use 1 - aggression
    "killer": 0.3,
    "coward": 1.0,
}
SAME_DISTRICT_ALLIANCE_CHANCE = 0.9  # chance to ally with your district partner (replaces the usual chance)
ALLIANCE_MERGE_CHANCE = 0.15  # chance two alliances meeting merge (if the result fits ALLIANCE_MAX_SIZE)
ALLIANCE_MAX_SIZE = 6
BETRAYAL_CHANCE_PER_MINUTE = 0.08  # for a member with aggression 1 (scaled by aggression)
ALLIANCE_AGGRESSION_BONUS = 0.2   # added to a group's chance to fight for each extra member
ALLIANCE_SENSE_RADIUS = 115 # members notice non-allies this far away (loners: VISION_RADIUS)
ALLY_STRENGTH_SHARE = 0.8   # share of a nearby ally's strength added in a fight...
ALLY_SUPPORT_RANGE = 110    # ...for allies this close
ALLIANCE_ASSIST_RADIUS = 250  # members this close to an ally's fight (or the leader's hunt) join in
ALLIANCE_RETREAT_SECONDS = 1  # alliances back off only this long after a fight (loners: RETREAT_SECONDS)
ALLY_SHARE_RANGE = 40       # allies this close hand over food/water
FOLLOW_SPREAD = 12          # members stay within about this distance of their leader...
FOLLOW_LEASH = 45           # ...collect loot at most this far from it...
FOLLOW_CATCHUP_MULTIPLIER = 1.3  # ...and hurry (this much faster) when further behind than that
CAREER_DISTRICTS = (1, 2, 4)  # like the books: these districts' tributes start the Games as one pack
CAMP_ALLIANCE_SIZE = 4      # alliances at least this big stay around the cornucopia...
CAMP_RADIUS = 350           # ...exploring only within this distance of it
ALLIANCE_NAMES = [          # a random one is given to each alliance
    "the Careers", "the Pack", "the Wolves", "the Mockingjays", "the Tracker Jackers",
    "the Hunters", "the Jabberjays", "the Lions", "the Victors-to-be", "the Nightlocks",
    "the Firebirds", "the Ravens", "the Vipers", "the Iron Circle", "the Outliers",
    "the Coal Diggers", "the Tide", "the Harvest", "the Sparks", "the Shadows",
]

# =============================================================================
# The Gamemakers and the Capitol
# =============================================================================
# Day and night
DAY_SECONDS = 90            # one full day (daytime + night)
NIGHT_SHARE = 0.4           # the last 40% of each day is night
NIGHT_DARKNESS = 150        # how dark the night overlay gets (0-255)
NIGHT_VISION_FACTOR = 0.7   # seeing distance at night
NIGHT_SLEEP_THRESHOLD = 97  # at night, tributes who aren't hunting sleep below this, until dawn
NIGHT_HUNT_MIN_FIGHT_CHANCE = 0.7  # tributes at least this likely to fight stay up at night to hunt
FALLEN_SHOW_SECONDS = 6     # the day's fallen are shown this long at nightfall

# Sponsor gifts
SPONSOR_CHECK_SECONDS = 12  # this often, one struggling tribute may get a gift
SPONSOR_BASE_CHANCE = 0.35  # chance per check
PARACHUTE_FALL_SECONDS = 2.5

# Fires, floods and mutts
GAMEMAKER_EVENT_SECONDS = (50, 80)  # time between Gamemaker events (random)
FIRE_RADIUS = 220           # a fire or flood covers a circle this big
FIRE_SECONDS = 18
FIRE_DAMAGE_CHANCE = 0.004  # chance per frame to die for a tribute caught inside
MUTT_COUNT = (2, 4)
MUTT_SECONDS = 25
MUTT_SPEED = 0.55
MUTT_KILL_CHANCE = 0.5      # chance a mutt that reaches a tribute kills it (else it escapes, injured)

# The end: feast, shrinking arena and finale
FEAST_PLAYERS = 8           # the feast is announced once this few tributes remain
FEAST_ITEMS = {"food": 6, "water": 6, "weapon": 4}
FEAST_DELAY_SECONDS = 8     # supplies appear this long after the announcement
SHRINK_START_PLAYERS = 6    # with this many left, the arena starts shrinking toward the cornucopia
SHRINK_MIN_RADIUS = 260
SHRINK_SECONDS = 200        # time to shrink from full size to the minimum
SHOWDOWN_PLAYERS = 4        # with this many left, the finale: alliances break up and all fight to the death at the cornucopia
FINALE_RADIUS = 250         # in the finale, tributes attack anyone this close to the cornucopia

# =============================================================================
# Terrain
# =============================================================================
TERRAIN_COLORS = {
    "meadow": (76, 98, 60),
    "forest": (40, 70, 47),
    "rock": (98, 96, 91),
    "sand": (152, 136, 96),
    "marsh": (52, 84, 88),
}
TERRAIN_WEIGHTS = {"meadow": 3, "forest": 3, "rock": 1.5, "sand": 1.2, "marsh": 1}  # how common each is
TERRAIN_ZONES = 22          # number of terrain areas
TERRAIN_WARP = 70           # how wavy the borders between areas are
TERRAIN_CLEAR_RADIUS = 320  # a meadow clearing surrounds the cornucopia
TERRAIN_VISIBILITY = {      # seeing distance factor; forest wins if either tribute is in it
    "forest": 0.5,          # forest hides
    "sand": 1.3,            # open ground
}
TERRAIN_SPEED = {"marsh": 0.6}  # movement speed factor
SAND_THIRST_FACTOR = 1.5    # thirst drops this much faster on sand
MARSH_REFILL_SECONDS = 60   # standing in marsh refills thirst from 0 to full in this time
MARSH_DRINK_UNTIL = 90      # a tribute drinking in marsh stays until thirst reaches this
MARSH_SEARCH_RADIUS = 600   # thirsty tributes look for marsh this far away

# =============================================================================
# Camera
# =============================================================================
CAMERA_MAX_ZOOM = 3.0       # most zoomed in (screen pixels per world pixel)
CAMERA_OPENING_ZOOM = 1.3   # while watching the countdown and bloodbath
CAMERA_CHASE_ZOOM = 1.8     # most zoomed in when framing a chase or two tributes
CAMERA_FIGHT_ZOOM = 2.4     # while watching a fight
CAMERA_FIGHT_LINGER_SECONDS = 0.5  # stays on a fight's spot this long after it ends
CAMERA_MUTT_RADIUS = 160    # shows a mutt this close to a tribute
CAMERA_SWITCH_COOLDOWN_SECONDS = 3  # stays on something at least this long before switching
CAMERA_SMOOTHING = 0.08     # how quickly the automatic camera glides (share of the gap per frame)
CAMERA_PAN_SPEED = 12       # screen pixels per frame when panning with W/A/S/D
CAMERA_ZOOM_STEP = 1.15     # zoom factor per mouse wheel notch

# =============================================================================
# Drawing
# =============================================================================
PLAYER_COLOR = (220, 220, 220)      # a tribute on its own (allies take their alliance's color)
LEADER_RING_COLOR = (255, 255, 255)
SELECT_RING_COLOR = (255, 230, 120) # around a clicked tribute
ALLIANCE_COLORS = [                 # each new alliance takes the next color
    (255, 120, 120), (120, 230, 120), (120, 160, 255), (255, 220, 100),
    (240, 120, 240), (110, 230, 230), (255, 170, 90), (190, 150, 255),
]
NAME_MIN_ZOOM = 0.7         # names above heads are hidden when zoomed out further than this
NAME_TEXT_COLOR = (235, 235, 235)
NEED_WARNING_COLORS = {     # warning dots above a tribute, one per need
    "hunger": (230, 140, 40),
    "thirst": (60, 140, 230),
    "sleep": (170, 90, 220),
}
WARNING_DOT_RADIUS = 2
WARNING_DOT_SPACING = 5
WARNING_DOT_OFFSET_Y = 4
WEAPON_ICON_COLOR = (200, 60, 60)   # small blade (or bow) under the dot = carries a weapon
SLEEP_ICON_COLOR = (180, 160, 255)  # small "z" under the dot = sleeping
INJURY_COLOR = (200, 30, 30)        # small cross on the dot = injured

LOOT_SIZE = 3
LOOT_COLORS = {
    "food": (230, 140, 40),     # orange, same as the hunger warning
    "water": (60, 140, 230),    # blue, same as the thirst warning
    "weapon": (200, 60, 60),    # red
}
CORNUCOPIA_SIZE = 70
CORNUCOPIA_COLOR = (216, 176, 82)
CORNUCOPIA_OUTLINE_COLOR = (110, 80, 25)
PLATE_RADIUS = 7
PLATE_COLOR = (70, 72, 76)
OUTSIDE_COLOR = (14, 15, 18)        # beyond the arena border
BORDER_COLOR = (95, 95, 85)

CHASE_LINE_COLOR = (130, 45, 45)    # faint line from a hunter to its prey
FIGHT_RING_COLOR = (255, 110, 60)   # pulsing ring around a fight in progress
FIGHT_FLASH_SECONDS = 0.5           # a red ring where a fight was decided
FIGHT_FLASH_COLOR = (255, 60, 60)
FIGHT_FLASH_RADIUS = 14
ALLIANCE_RING_SECONDS = 0.8         # a bigger ring in the alliance's color flashes where an alliance forms or grows
ALLIANCE_RING_RADIUS = 32
DEATH_MARK_SECONDS = 20             # a small cross where a tribute fell...
OPENING_DEATH_MARK_SECONDS = 4      # ...shorter during the crowded bloodbath
DEATH_MARK_COLOR = (230, 230, 230)
PARACHUTE_COLOR = (235, 235, 245)
FIRE_COLOR = (230, 90, 30)
FLOOD_COLOR = (60, 110, 200)
MUTT_COLOR = (40, 20, 20)
SHRINK_COLOR = (120, 30, 30)

# Screen overlays
COUNTDOWN_TEXT_COLOR = (255, 230, 150)
WIN_BANNER_SECONDS = 4      # the winner's name is shown this long before the debrief
MINIMAP_WIDTH = 200
MINIMAP_BORDER = (160, 160, 160)
CARD_WIDTH = 300            # tribute and alliance cards (top left)
FEED_MAX_LINES = 6          # event feed (bottom left): most lines at once...
FEED_SECONDS = 10           # ...each shown this long
FEED_LINE_HEIGHT = 18
FEED_TEXT_COLOR = (235, 235, 235)
FEED_SHADOW_COLOR = (0, 0, 0)
EVENT_COLORS = {            # feed and story colors per kind of event
    "info": (235, 235, 235),
    "kill": (255, 120, 110),
    "death": (230, 170, 120),
    "alliance": (130, 180, 255),
    "gamemaker": (240, 200, 90),
    "sponsor": (150, 230, 150),
    "fight": (210, 210, 210),
}
VISION_CIRCLE_COLOR = (55, 55, 55)  # debug view (Tab)
LEGEND_TEXT_COLOR = (200, 200, 200)
TOAST_SECONDS = 2.5         # a short headline in the top middle when a tribute falls
TRIBUTE_PANEL_WIDTH = 200   # the list of all tributes on the right (T toggles it)
FAST_FORWARD_FACTOR = 1.5    # quiet stretches (no fights, chases or mutts) run this much faster (G toggles it)
