"""Hunger Games-style descriptions for the event feed. Every kind of event
has a long list of lines; one is picked at random each time so the feed
doesn't repeat itself. In a line, {killer}, {victim} and so on are replaced
by names with str.format (e.g. "{a} meets {b}".format(a="Rue", b="Thresh"))."""
import random


def pick(lines, **names):
    """A random line from `lines`, with the names filled in."""
    return random.choice(lines).format(**names)


GAMES_BEGIN = [
    "The gong sounds. Let the Seventy-Fourth Hunger Games begin!",
    "The countdown hits zero and the tributes leap from their plates!",
    "Claudius Templesmith's voice booms: \"Let the Games begin!\"",
    "The gong echoes across the arena. May the odds be ever in your favor.",
    "Sixty seconds are up. The tributes explode off their platforms!",
    "The plates release their tributes. The Games are on!",
    "A deafening gong, and twenty-four tributes break into motion.",
    "The Capitol holds its breath as the Games begin.",
]

# Killed in a fight while the killer carried a weapon
KILL_ARMED = [
    "{killer}'s blade finds {victim}. A cannon fires.",
    "{victim} falls to {killer}'s weapon. BOOM goes the cannon.",
    "{killer} drives a knife into {victim}. The cannon sounds.",
    "A spear from {killer} ends {victim}'s Games.",
    "{killer} cuts {victim} down without hesitation.",
    "{victim} never saw {killer}'s blade coming.",
    "{killer} strikes true. {victim}'s cannon echoes through the arena.",
    "Steel flashes, and {victim} crumples before {killer}.",
    "{killer} buries an axe in {victim}. The Capitol roars.",
    "{victim} raises their hands too late. {killer} doesn't miss.",
    "An arrow from {killer} silences {victim} for good.",
    "{killer} finishes {victim} with a single swing. A cannon booms.",
    "{victim} bleeds out at the feet of {killer}.",
    "{killer} pins {victim} down and ends it with a blade.",
    "The sponsors cheer as {killer}'s weapon claims {victim}.",
]

# Killed in a fight by an unarmed killer
KILL_UNARMED = [
    "{killer} overpowers {victim} with bare hands. A cannon fires.",
    "{killer} snaps {victim}'s neck. BOOM.",
    "{victim} is strangled by {killer}. The cannon sounds.",
    "{killer} smashes a rock down on {victim}. It's over.",
    "{killer} wrestles {victim} to the ground and doesn't let go.",
    "{victim} loses a brutal fistfight to {killer}. A cannon booms.",
    "{killer} chokes the life out of {victim}.",
    "{victim} is beaten down by {killer}, who fights like a cornered animal.",
    "{killer} slams {victim} against a tree. {victim} doesn't get up.",
    "No weapon needed: {killer} ends {victim} with raw strength.",
    "{killer} tackles {victim} and holds them down until the cannon fires.",
    "{victim} underestimated {killer}. A fatal mistake.",
    "{killer} grabs a branch and brings it down on {victim}.",
    "A savage struggle ends with {victim} lifeless beneath {killer}.",
]

# Extra lines only used for kills during the bloodbath
KILL_BLOODBATH = [
    "{killer} cuts down {victim} at the mouth of the cornucopia.",
    "{victim} reaches for a backpack. {killer} reaches {victim} first.",
    "Blood on the cornucopia steps: {killer} claims {victim}.",
    "{victim} dies in the bloodbath, struck down by {killer}.",
    "{victim} gambled on the cornucopia and lost to {killer}.",
    "In the chaos around the horn, {killer} ends {victim}.",
    "{victim} barely steps off the plate before {killer} strikes.",
    "{killer} leaves {victim} among the scattered supplies.",
    "The golden horn claims another: {victim}, killed by {killer}.",
]

DEATH_HUNGER = [
    "{victim} succumbs to starvation. A cannon fires.",
    "Hunger finally claims {victim}.",
    "{victim}, too weak to hunt, starves to death.",
    "{victim} collapses, stomach empty. The cannon sounds.",
    "The arena starves {victim} out. BOOM.",
    "{victim} dies dreaming of bread from home.",
    "Days without food take their toll. {victim} is gone.",
    "{victim} wasted away, forgotten by the sponsors.",
    "No parachute came. {victim} starves.",
    "{victim} chews on bark one last time and does not wake up.",
]

DEATH_THIRST = [
    "{victim} dies of thirst. A cannon fires.",
    "Dehydration takes {victim}. The cannon sounds.",
    "{victim} never found water in time.",
    "{victim} collapses, lips cracked and dry. BOOM.",
    "The arena's heat bakes {victim} to death.",
    "{victim} crawls toward a mirage and never gets up.",
    "Without water, {victim} fades away.",
    "{victim} dies of thirst, the sponsors silent.",
    "{victim}'s tongue swells shut. The cannon booms.",
    "Thirst claims {victim} before any tribute could.",
]

DEATH_SLEEP = [
    "{victim} dies of exhaustion. A cannon fires.",
    "{victim} pushes on one step too far and never wakes.",
    "Exhaustion claims {victim}. The cannon sounds.",
    "{victim}'s body finally gives out.",
    "Too tired to go on, {victim} slips away.",
    "{victim} closes their eyes for the last time.",
]

DEATH_OTHER = [
    "{victim} dies. A cannon fires.",
    "The arena claims {victim}. BOOM.",
]

REMAINING = [
    "{n} tributes remain.",
    "{n} left.",
    "{n} tributes still alive.",
    "Only {n} remain.",
    "{n} tributes are left in the arena.",
]
REMAINING_ONE_LEFT = ["One tribute remains."]

ALLIANCE_FORMED = [
    "{names} shake hands and form an alliance. {leader} takes charge.",
    "An uneasy truce: {names} team up, led by {leader}.",
    "{names} agree to watch each other's backs, with {leader} in the lead.",
    "A pact is sealed between {names}. {leader} gives the orders.",
    "{names} join forces. The sponsors love an alliance. {leader} leads.",
    "{names} decide they're stronger together. {leader} is in charge.",
    "Nods are exchanged and weapons lowered: {names} are allies now, under {leader}.",
    "{leader} convinces {others} to join forces.",
    "{names} strike a deal to hunt together, with {leader} calling the shots.",
    "In the arena, trust is rare. {names} give it a try, led by {leader}.",
]

ALLIANCE_FORMED_BLOODBATH = [
    "At the cornucopia, {names} band together, led by {leader}.",
    "{leader} and {others} fight their way to the horn side by side and stay together.",
    "Amid the bloodbath, {names} stand back to back. {leader} leads the pack.",
    "{names} claim the cornucopia together under {leader}.",
    "Blood still wet on their hands, {names} form a pack. {leader} leads.",
]

ALLIANCE_JOINED = [
    "{newcomer} joins {leader}'s alliance.",
    "{leader}'s group welcomes {newcomer} into the fold.",
    "{newcomer} throws in their lot with {leader}'s alliance.",
    "{newcomer} begs to join {leader}'s pack, and is let in.",
    "{leader} offers {newcomer} a place in the alliance. {newcomer} accepts.",
    "{newcomer} lowers their weapon and joins {leader}'s alliance.",
    "The alliance led by {leader} grows: {newcomer} is in.",
    "{newcomer} decides it's safer with {leader}'s group.",
    "{newcomer} earns a place among {leader}'s allies.",
]

ALLIANCE_MERGED = [
    "Two alliances become one: {names}, led by {leader}.",
    "Rather than fight, two packs join forces. {leader} leads {names}.",
    "A powerful new alliance forms as two groups merge under {leader}: {names}.",
    "The sponsors gasp as two alliances unite behind {leader}.",
    "{leader} brokers a deal between two groups. Together: {names}.",
    "Two groups meet, weapons ready, and choose peace. {leader} now leads {names}.",
]

ALLIANCE_BROKE_UP = {
    "betrayal": [
        "The betrayal shatters what was left of the alliance of {names}.",
        "With trust gone, {names} go their separate ways.",
        "The alliance of {names} dies with the betrayal.",
    ],
    "too few members left": [
        "With too few left, the alliance of {names} dissolves.",
        "{names} are all that's left of their alliance, and it falls apart.",
        "The alliance of {names} is no more. It's every tribute for themself.",
        "Death has broken the alliance of {names}.",
    ],
    "the finale has begun": [
        "The finale is here. The alliance of {names} is over.",
        "{names} look at each other differently now. The alliance ends.",
        "Only one can win: {names} break their alliance.",
        "Friends no more. {names} part ways for the finale.",
    ],
    "only allies are left": [
        "Only allies remain, and only one can go home. {names} turn on each other.",
        "The last tributes are all allies. The alliance of {names} breaks.",
        "{names} realize the truth: only one can win. The alliance is over.",
    ],
}
ALLIANCE_BROKE_UP_OTHER = ["The alliance of {names} falls apart."]

# When only one member is left to leave, the lines above would read oddly
ALLIANCE_LAST_MEMBER = [
    "{names} is the last of their alliance, and alone once more.",
    "With their allies gone, {names} is on their own again.",
    "{names} buries the memory of their alliance and walks on alone.",
    "Nobody is left to watch {names}'s back. The alliance is over.",
    "{names} is all that remains of a once-proud alliance.",
]

BETRAYAL = [
    "{traitor} turns on the alliance and goes for {victim}!",
    "{traitor} betrays their allies, drawing a blade on {victim}!",
    "Trust shattered: {traitor} attacks {victim}!",
    "{traitor} waited for this moment. {victim} is the target.",
    "In the dead of night, {traitor} turns on {victim}!",
    "{traitor} decides an alliance can't win the Games, and goes after {victim}.",
    "{traitor} breaks the pact and lunges at {victim}!",
    "The Capitol loves a betrayal: {traitor} turns on {victim}!",
    "{victim} turns their back for one second too long. {traitor} strikes.",
    "{traitor} was never really an ally. {victim} finds out the hard way.",
]

NEW_LEADER = [
    "{leader} takes command of the alliance.",
    "{leader} steps up to lead the group.",
    "The alliance looks to {leader} now.",
    "{leader} is the new leader of the pack.",
    "With their leader gone, the group follows {leader}.",
    "{leader} claims the lead of the alliance.",
]

ESCAPE = [
    "{loser} is beaten by {winner} but flees, dropping supplies.",
    "{loser} breaks free from {winner} and runs for their life.",
    "Wounded, {loser} escapes {winner}'s grasp.",
    "{loser} throws down their pack and escapes {winner}.",
    "{winner} almost has {loser}, but {loser} slips away.",
    "{loser} scrambles into the trees, leaving {winner} behind.",
    "Bleeding but alive, {loser} outruns {winner}.",
    "{loser} kicks free of {winner} and bolts.",
    "{winner} wins the scuffle, but {loser} lives to fight another day.",
]

STANDOFF = [
    "{a} and {b} circle each other, then both back away.",
    "{a} and {b} size each other up. Neither strikes.",
    "A tense standoff: {a} and {b} retreat without a blow.",
    "{a} and {b} trade glares and go their separate ways.",
    "{a} and {b} decide today is not the day.",
    "Weapons raised, {a} and {b} slowly step apart.",
    "{a} and {b} clash briefly, then think better of it.",
]

MUTUAL_LOSS = [
    "{a} and {b} wound each other and stagger apart.",
    "A bloody exchange: {a} and {b} both limp away hurt.",
    "{a} and {b} fight to exhaustion. Both lose supplies.",
    "{a} and {b} tear into each other. Nobody wins.",
    "Both {a} and {b} are hurt in a vicious brawl.",
    "{a} and {b} land blows and flee in opposite directions.",
    "Supplies scatter as {a} and {b} brawl to a draw.",
]

BLOODBATH_OVER = [
    "The bloodbath is over. {n} cannons fire, one for each fallen tribute.",
    "The cornucopia falls quiet. {n} tributes lie dead.",
    "The survivors scatter from the horn. The bloodbath claimed {n}.",
    "{n} cannons boom in a row: the bloodbath is over.",
    "The dust settles at the cornucopia. {n} tributes did not make it.",
    "Hovercraft collect {n} bodies from around the cornucopia.",
]
BLOODBATH_OVER_NONE = [
    "The bloodbath is over, and somehow, every tribute survived it.",
    "The cornucopia empties without a single cannon. The Capitol is disappointed.",
]

FINALE = [
    "The finale! The Gamemakers drive the last {n} tributes to the cornucopia.",
    "{n} tributes remain. The arena shrinks them toward the horn for a fight to the death.",
    "A thunderous announcement: the final {n} must meet at the cornucopia.",
    "Feast time is over. The last {n} tributes converge on the cornucopia.",
    "The Gamemakers have had enough waiting. The final {n} are herded to the horn.",
    "Only {n} remain. The end of the Games is near.",
]

WINNER = [
    "{winner} is the victor of the Hunger Games, with {kills} kill(s)!",
    "Trumpets blare: {winner} has won the Games! ({kills} kill(s))",
    "Ladies and gentlemen, the victor: {winner}! ({kills} kill(s))",
    "{winner} stands alone in the arena. The Games are won, with {kills} kill(s).",
    "The last cannon fires. {winner} is going home, with {kills} kill(s).",
    "{winner} survives it all and is crowned victor ({kills} kill(s)).",
]

NO_SURVIVORS = [
    "The final cannons fire together. There is no victor.",
    "No tribute survives. The Capitol is stunned into silence.",
]


ALLIANCE_NAMED = [
    "They call themselves {alliance}.",
    "The Capitol already calls them {alliance}.",
    "The commentators dub them {alliance}.",
    "Soon the whole of Panem knows them as {alliance}.",
]

SPONSOR_GIFT = [
    "A silver parachute drifts down to {name}: {item}!",
    "A sponsor sends {name} {item}. Someone out there is betting on them.",
    "Chimes ring out as a parachute lands beside {name} carrying {item}.",
    "{name} looks up to see a silver parachute with {item}.",
    "Haymitch would be proud: {name} receives {item} from a sponsor.",
    "The sponsors reward {name} with {item}.",
]

FIRE = [
    "The Gamemakers set the {area} ablaze! Tributes run from the flames.",
    "A wall of fire sweeps through the {area}!",
    "Fireballs rain down on the {area}. The Gamemakers want action.",
    "Smoke billows as the {area} bursts into flames.",
]
FLOOD = [
    "Water surges through the {area}! The Gamemakers have opened the floodgates.",
    "A sudden flood swallows the {area}!",
    "The ground in the {area} turns to rushing water.",
]
MUTTS = [
    "A howl echoes through the arena. The Gamemakers have released {n} mutts!",
    "{n} snarling mutts burst from the {area}!",
    "Something unnatural stalks the {area}: {n} mutts are loose.",
    "The Gamemakers unleash {n} wolf-like mutts on the tributes.",
]
MUTT_KILL = [
    "Mutts tear {victim} apart. A cannon fires.",
    "{victim} can't outrun the mutts. BOOM.",
    "The mutts drag {victim} down. The cannon sounds.",
    "{victim} falls to the Gamemakers' beasts.",
]
MUTT_ESCAPE = [
    "{victim} fights off a mutt, but is badly hurt.",
    "{victim} escapes the mutts, bleeding.",
    "A mutt's claws rake {victim}, who barely gets away.",
]
FIRE_KILL = [
    "{victim} is caught in the flames. A cannon fires.",
    "The fire claims {victim}. BOOM.",
    "{victim} couldn't escape the Gamemakers' fire.",
]
FLOOD_KILL = [
    "{victim} is swept away by the flood. A cannon fires.",
    "The rushing water drowns {victim}.",
    "{victim} disappears beneath the floodwater. BOOM.",
]
SHRINK = [
    "The arena begins to close in. The Gamemakers force the last tributes together.",
    "A deadly force field starts to shrink toward the cornucopia.",
    "The edges of the arena turn deadly. Everyone must move inward.",
]
SHRINK_KILL = [
    "{victim} is caught outside the shrinking arena. A cannon fires.",
    "The closing boundary claims {victim}.",
]
FEAST_ANNOUNCED = [
    "Claudius Templesmith announces a feast at the cornucopia! Each tribute needs something desperately.",
    "\"Attention, tributes!\" A feast will be held at the cornucopia.",
    "The Gamemakers invite the tributes to a feast at the cornucopia. Few will refuse.",
]
FEAST_READY = [
    "The feast table rises at the cornucopia, loaded with supplies.",
    "Supplies appear at the cornucopia. The feast has begun.",
]
HIDE = [
    "{name} scrambles up a tree to hide.",
    "{name} vanishes into the branches above.",
    "{name} climbs out of reach and holds perfectly still.",
    "{name} hides high in the canopy, heart pounding.",
]
AMBUSH_SET = [
    "{name} lies in wait by the {spot}.",
    "{name} sets a trap near the {spot} and waits.",
    "{name} crouches in the undergrowth near the {spot}, watching.",
]
AMBUSH_SPRUNG = [
    "{killer} springs the ambush on {victim}!",
    "{victim} walks straight into {killer}'s trap!",
    "Out of nowhere, {killer} leaps at {victim}!",
]
REVENGE_SWORN = [
    "{name} swears vengeance on {killer} for their district partner.",
    "{name} will not forget what {killer} did to their district partner.",
    "Grief turns to rage: {name} is hunting {killer}.",
]
REVENGE_DONE = [
    "{killer} avenges their district partner. {victim} is dead.",
    "Revenge: {killer} kills {victim}, their district partner's killer.",
]
FEARED = [
    "{name} has {kills} kills. The other tributes fear them now.",
    "With {kills} kills, {name} is the most dangerous tribute in the arena.",
    "Panem whispers {name}'s name: {kills} kills and counting.",
]
NIGHTFALL = [
    "Night falls on day {day}. The anthem plays and the fallen appear in the sky.",
    "Darkness settles over the arena. Day {day} is over.",
    "The Capitol seal lights the sky at the end of day {day}.",
]
NIGHTFALL_NONE = [
    "Night falls on day {day}. No faces appear in the sky tonight.",
    "The anthem plays after day {day}, but the sky stays empty.",
]
DAWN = [
    "Dawn breaks over the arena. Day {day} begins.",
    "The sun rises on day {day} of the Games.",
]


def kill(victim, killer, armed, bloodbath):
    lines = KILL_ARMED if armed else KILL_UNARMED
    if bloodbath:
        lines = lines + KILL_BLOODBATH  # + joins the two lists
    return pick(lines, victim=victim, killer=killer)


def death(victim, cause):
    lines = {"hunger": DEATH_HUNGER, "thirst": DEATH_THIRST, "sleep": DEATH_SLEEP,
             "fire": FIRE_KILL, "flood": FLOOD_KILL, "mutts": MUTT_KILL, "arena": SHRINK_KILL}
    return pick(lines.get(cause, DEATH_OTHER), victim=victim)


def remaining(n):
    return pick(REMAINING_ONE_LEFT if n == 1 else REMAINING, n=n)


def alliance_formed(alliance, bloodbath):
    lines = ALLIANCE_FORMED + (ALLIANCE_FORMED_BLOODBATH if bloodbath else [])
    others = ", ".join(member.name for member in alliance.members if member is not alliance.leader)
    line = pick(lines, names=alliance.names(), leader=alliance.leader.name, others=others)
    return line + " " + pick(ALLIANCE_NAMED, alliance=alliance.name)


def alliance_broke_up(alliance, reason):
    if len(alliance.members) == 1:
        return pick(ALLIANCE_LAST_MEMBER, names=alliance.names())
    return pick(ALLIANCE_BROKE_UP.get(reason, ALLIANCE_BROKE_UP_OTHER), names=alliance.names())


def bloodbath_over(n):
    return pick(BLOODBATH_OVER if n > 0 else BLOODBATH_OVER_NONE, n=n)
