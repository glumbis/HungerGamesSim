"""The camera decides which part of the large arena the window shows, and
how zoomed in it is. World coordinates are positions in the arena; screen
coordinates are pixels in the window."""
import pygame

from ai import HUNTING, SEARCHING
from config import (
    WORLD_WIDTH, WORLD_HEIGHT,
    CAMERA_MAX_ZOOM, CAMERA_OPENING_ZOOM, CAMERA_CHASE_ZOOM,
    CAMERA_SMOOTHING, CAMERA_PAN_SPEED, CAMERA_ZOOM_STEP,
)
from utils import distance


class Camera:
    def __init__(self, x, y, zoom):
        self.x = x              # world point shown in the middle of the window
        self.y = y
        self.zoom = zoom        # screen pixels per world pixel (2 = everything twice as big)
        self.auto = True        # True: the camera follows the action by itself
        self.dragging = False   # True while the left mouse button drags the view
        self.focus = None       # the hunter whose chase the automatic camera is following

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
            # when far away, gentle when close
            self.x += (target_x - self.x) * CAMERA_SMOOTHING
            self.y += (target_y - self.y) * CAMERA_SMOOTHING
            self.zoom += (target_zoom - self.zoom) * CAMERA_SMOOTHING
        self.clamp(screen)

    def choose_focus(self, sim, screen):
        """Where the automatic camera wants to look, and how zoomed in:
        1. the cornucopia during the countdown and the bloodbath
        2. a chase: a hunter and the player it is after, framed together.
           The camera sticks with one hunter while its chase lasts; when it
           needs a new one, it picks the chase closest to where it looks now.
        3. otherwise all living players, zoomed out just enough to fit them"""
        arena = sim.arena
        if not sim.opening_over:
            return arena.center_x, arena.center_y, CAMERA_OPENING_ZOOM
        if not sim.players:
            return self.x, self.y, self.zoom

        def is_chasing(player):
            return (player.alive and player.state in (HUNTING, SEARCHING)
                    and player.prey is not None and player.prey.alive)

        if self.focus is None or not is_chasing(self.focus):
            hunters = [player for player in sim.players if is_chasing(player)]
            self.focus = min(hunters, default=None,
                             key=lambda hunter: distance(hunter.x, hunter.y, self.x, self.y))
        if self.focus is not None:
            return self.frame([self.focus, self.focus.prey], screen)
        return self.frame(sim.players, screen)

    def frame(self, players, screen):
        """Center on a group of players, zoomed so they all fit with some
        space around them (but never closer than CAMERA_CHASE_ZOOM)."""
        xs = [player.x for player in players]
        ys = [player.y for player in players]
        margin = 150  # world pixels of space around the outermost players
        width, height = screen.get_size()
        box_width = max(xs) - min(xs) + 2 * margin
        box_height = max(ys) - min(ys) + 2 * margin
        zoom = min(width / box_width, height / box_height, CAMERA_CHASE_ZOOM)
        return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(zoom, self.min_zoom(screen))
