"""The camera decides which part of the large arena the window shows, and
how zoomed in it is. World coordinates are positions in the arena; screen
coordinates are pixels in the window."""
import pygame

from ai import HUNTING, SEARCHING
from config import (
    WORLD_WIDTH, WORLD_HEIGHT, FPS, CAMERA_FIGHT_LINGER_SECONDS,
    CAMERA_MAX_ZOOM, CAMERA_OPENING_ZOOM, CAMERA_CHASE_ZOOM, CAMERA_FIGHT_ZOOM,
    CAMERA_SMOOTHING, CAMERA_PAN_SPEED, CAMERA_ZOOM_STEP, CAMERA_MUTT_RADIUS,
    CAMERA_SWITCH_COOLDOWN_SECONDS,
)
from utils import distance


def is_chasing(player):
    return (player.alive and player.state in (HUNTING, SEARCHING)
            and player.prey is not None and player.prey.alive)


class Camera:
    def __init__(self, x, y, zoom):
        self.x = x              # world point shown in the middle of the window
        self.y = y
        self.zoom = zoom        # screen pixels per world pixel (2 = everything twice as big)
        self.auto = True        # True: the camera follows the action by itself
        self.dragging = False   # True while the left mouse button drags the view
        # What the automatic camera is showing, as a tuple:
        # ("fight", fight), ("mutt", mutt, player), ("chase", hunter), ("pair", a, b), or None
        self.subject = None
        self.switch_timer = 0   # frames before it may switch to something else
        self.linger_frames = 0  # frames left to stay on a fight's spot after it ends
        self.watched = []       # the tributes the automatic camera is showing (their cards are shown)

    # --- Converting between world and screen coordinates ----------------

    def world_to_screen(self, x, y, screen):
        width, height = screen.get_size()
        return (int((x - self.x) * self.zoom + width / 2),
                int((y - self.y) * self.zoom + height / 2))

    def screen_to_world(self, screen_x, screen_y, screen):
        width, height = screen.get_size()
        return ((screen_x - width / 2) / self.zoom + self.x,
                (screen_y - height / 2) / self.zoom + self.y)

    def size(self, length, minimum=1):
        """A world length in screen pixels, never smaller than `minimum`
        (so small things stay visible when zoomed far out)."""
        return max(minimum, int(length * self.zoom))

    def min_zoom(self, screen):
        """The zoom at which the whole arena just fits in the window."""
        width, height = screen.get_size()
        return min(width / WORLD_WIDTH, height / WORLD_HEIGHT)

    def clamp(self, screen):
        """Keep the zoom within its limits and the view centered over the arena."""
        self.zoom = max(self.min_zoom(screen), min(self.zoom, CAMERA_MAX_ZOOM))
        self.x = max(0, min(self.x, WORLD_WIDTH))
        self.y = max(0, min(self.y, WORLD_HEIGHT))

    # --- Manual control ----------------------------------------------------

    def handle_event(self, event, screen):
        """Mouse wheel zooms, dragging moves the view, F = automatic camera,
        C = show the whole arena. Any manual move switches automatic mode off."""
        if event.type == pygame.MOUSEWHEEL:
            # Zoom toward the mouse: the world point under the mouse stays put
            mouse_x, mouse_y = pygame.mouse.get_pos()
            before = self.screen_to_world(mouse_x, mouse_y, screen)
            self.zoom *= CAMERA_ZOOM_STEP ** event.y  # ** means "to the power of"
            self.clamp(screen)
            after = self.screen_to_world(mouse_x, mouse_y, screen)
            self.x += before[0] - after[0]
            self.y += before[1] - after[1]
            self.auto = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            move_x, move_y = event.rel  # how far the mouse moved since the last event
            self.x -= move_x / self.zoom
            self.y -= move_y / self.zoom
            self.auto = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                self.auto = True
            elif event.key == pygame.K_c:
                self.auto = False
                self.x, self.y = WORLD_WIDTH / 2, WORLD_HEIGHT / 2
                self.zoom = self.min_zoom(screen)
        self.clamp(screen)

    # --- Every frame -------------------------------------------------------

    def update(self, sim, screen):
        """Pan with W/A/S/D (held down), then, in automatic mode, glide
        toward whatever deserves attention."""
        keys = pygame.key.get_pressed()
        # True counts as 1 and False as 0, so this gives -1, 0 or +1
        pan_x = keys[pygame.K_d] - keys[pygame.K_a]
        pan_y = keys[pygame.K_s] - keys[pygame.K_w]
        if pan_x or pan_y:
            self.x += pan_x * CAMERA_PAN_SPEED / self.zoom
            self.y += pan_y * CAMERA_PAN_SPEED / self.zoom
            self.auto = False

        if self.auto:
            target_x, target_y, target_zoom = self.choose_focus(sim, screen)
            # Move a small share of the remaining distance each frame: fast
            # when far away, gentle when close. Fights are short, so get there
            # twice as quickly.
            on_fight = self.subject is not None and self.subject[0] == "fight"
            smoothing = CAMERA_SMOOTHING * 2 if on_fight else CAMERA_SMOOTHING
            self.x += (target_x - self.x) * smoothing
            self.y += (target_y - self.y) * smoothing
            self.zoom += (target_zoom - self.zoom) * smoothing
        self.clamp(screen)

    def choose_focus(self, sim, screen):
        """Where the automatic camera wants to look, and how zoomed in.
        During the countdown and bloodbath it shows the whole cornucopia area.
        Afterwards it picks the most interesting thing (see best_subject), but
        once it shows something it stays on it for at least
        CAMERA_SWITCH_COOLDOWN_SECONDS, unless that is over, so the view
        doesn't jump around. It also remembers whom it shows (self.watched)."""
        arena = sim.arena
        self.watched = []
        if not sim.opening_over:
            return arena.center_x, arena.center_y, CAMERA_OPENING_ZOOM
        if not sim.players:
            return self.x, self.y, self.zoom

        if self.switch_timer > 0:
            self.switch_timer -= 1
        if self.subject is not None and self.subject[0] == "fight" and self.subject[1] not in arena.fights:
            self.linger_frames -= 1  # the fight is decided: stay on its spot a moment longer

        best = self.best_subject(sim)
        current_ok = self.still_on(self.subject, sim)
        if best != self.subject and (self.switch_timer == 0 or not current_ok):
            self.subject = best
            self.switch_timer = int(CAMERA_SWITCH_COOLDOWN_SECONDS * FPS)
            if best is not None and best[0] == "fight":
                self.linger_frames = int(CAMERA_FIGHT_LINGER_SECONDS * FPS)
        return self.show(self.subject, sim, screen)

    def best_subject(self, sim):
        """The most interesting thing to show right now:
        1. the fight being watched, until it is decided (and a moment after)
        2. another fight (the one closest to the view)
        3. a mutt close to a tribute
        4. a chase (the same hunter while its chase lasts)
        5. the two non-allied tributes closest to each other"""
        arena = sim.arena
        if self.subject is not None and self.subject[0] == "fight" and self.still_on(self.subject, sim):
            return self.subject
        if arena.fights:
            fight = min(arena.fights, key=lambda fight: distance(fight.x, fight.y, self.x, self.y))
            return ("fight", fight)

        encounters = [(distance(mutt.x, mutt.y, player.x, player.y), mutt, player)
                      for mutt in sim.gamemakers.mutts for player in sim.players]
        if encounters:
            gap, mutt, player = min(encounters, key=lambda encounter: encounter[0])
            if gap <= CAMERA_MUTT_RADIUS:
                return ("mutt", mutt, player)

        if self.subject is not None and self.subject[0] == "chase" and is_chasing(self.subject[1]):
            return self.subject
        hunters = [player for player in sim.players if is_chasing(player)]
        if hunters:
            hunter = min(hunters, key=lambda hunter: distance(hunter.x, hunter.y, self.x, self.y))
            return ("chase", hunter)

        pair = self.closest_pair(sim.players)
        if pair is not None:
            first, second = sorted(pair, key=lambda player: player.id)  # same pair = same tuple
            return ("pair", first, second)
        return None

    def still_on(self, subject, sim):
        """True if what `subject` shows is still going on."""
        if subject is None:
            return False
        kind = subject[0]
        if kind == "fight":
            return subject[1] in sim.arena.fights or self.linger_frames > 0
        if kind == "mutt":
            _, mutt, player = subject
            return mutt in sim.gamemakers.mutts and player.alive and \
                distance(mutt.x, mutt.y, player.x, player.y) <= CAMERA_MUTT_RADIUS * 1.5
        if kind == "chase":
            return is_chasing(subject[1])
        _, first, second = subject  # a pair
        return first.alive and second.alive

    def show(self, subject, sim, screen):
        """The view (x, y, zoom) for a subject, and whom it shows."""
        if subject is None:
            return self.frame(sim.players, screen)
        kind = subject[0]
        if kind == "fight":
            fight = subject[1]
            self.watched = [fight.attacker, fight.defender]
            return fight.x, fight.y, CAMERA_FIGHT_ZOOM
        if kind == "mutt":
            _, mutt, player = subject
            self.watched = [player]
            return self.frame([mutt, player], screen)
        if kind == "chase":
            hunter = subject[1]
            if hunter.prey is None:
                self.watched = [hunter]
                return self.frame([hunter], screen)
            self.watched = [hunter, hunter.prey]
            return self.frame([hunter, hunter.prey], screen)
        _, first, second = subject
        self.watched = [first, second]
        return self.frame([first, second], screen)

    def closest_pair(self, players):
        """The two players nearest to each other, or None if there are fewer
        than two. Allies stick together, so an allied pair only counts if
        there is no other pair."""
        best, best_gap = None, float("inf")  # float("inf") = bigger than any number
        for i, first in enumerate(players):
            for second in players[i + 1:]:  # each pair once
                gap = distance(first.x, first.y, second.x, second.y)
                if first.alliance is not None and first.alliance is second.alliance:
                    gap += 100000  # allies: only if nothing else is available
                if gap < best_gap:
                    best, best_gap = (first, second), gap
        return best

    def frame(self, players, screen):
        """Center on a group of players (or anything with x and y), zoomed so
        they all fit with some space around them (but never closer than
        CAMERA_CHASE_ZOOM)."""
        xs = [player.x for player in players]
        ys = [player.y for player in players]
        margin = 150  # world pixels of space around the outermost players
        width, height = screen.get_size()
        box_width = max(xs) - min(xs) + 2 * margin
        box_height = max(ys) - min(ys) + 2 * margin
        zoom = min(width / box_width, height / box_height, CAMERA_CHASE_ZOOM)
        return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(zoom, self.min_zoom(screen))
