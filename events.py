"""The event feed: key moments (eliminations, alliance news, the winner)
shown in the bottom-left corner of the screen and printed to the terminal."""
from collections import Counter

import pygame

from config import (
    FPS,
    FEED_MAX_LINES, FEED_SECONDS, FEED_LINE_HEIGHT, FEED_TEXT_COLOR, FEED_SHADOW_COLOR,
    EVENT_COLORS, OPENING_DEATH_MARK_SECONDS,
)

entries = []     # events on screen, oldest first; each is [text, frames_left]
history = []     # every event of the current game, oldest first (for the debrief)
frame_count = 0  # frames since the start, used for the timestamps
counts = Counter()  # how often some things happened, e.g. counts["betrayals"] (for the debrief)
history_kinds = []  # the kind of each event in `history` (same order)
markers = []        # short-lived symbols in the arena, each [x, y, kind, frames_left] ("heart", "broken", "death")
opening = True      # True during the countdown and bloodbath (set by main.Simulation)


def reset():
    """Forget everything, ready for a new game."""
    global frame_count, opening  # see update() for what `global` does
    opening = True
    entries.clear()
    history.clear()
    history_kinds.clear()
    markers.clear()
    counts.clear()
    frame_count = 0


def log(text, kind="info"):
    """Record an event: print it, add it to the on-screen feed and keep it
    in the history. `kind` ("kill", "alliance", ...) picks its color."""
    minutes, seconds = divmod(frame_count // FPS, 60)  # divmod gives (whole minutes, leftover seconds)
    stamped = f"{minutes}:{seconds:02d}  {text}"         # :02d pads to two digits, e.g. 1:05
    print(stamped)
    history.append(stamped)
    history_kinds.append(kind)
    entries.append([stamped, FEED_SECONDS * FPS, kind])
    del entries[:-FEED_MAX_LINES]  # keep only the newest FEED_MAX_LINES events


def update():
    """Advance the clock by one frame and drop events whose time is up."""
    # `global` lets this function change the module-level variable
    # instead of creating a new local one
    global frame_count
    frame_count += 1
    for entry in entries:
        entry[1] -= 1
    entries[:] = [entry for entry in entries if entry[1] > 0]  # [:] replaces the contents in place
    for marker in markers:
        marker[3] -= 1
    markers[:] = [marker for marker in markers if marker[3] > 0]


def add_marker(x, y, kind, seconds):
    """Show a symbol ("heart", "broken" or "death") at a spot in the arena for a while.
    During the opening the cornucopia is crowded enough: no hearts, and
    crosses fade quickly."""
    if opening:
        if kind != "death":
            return
        seconds = min(seconds, OPENING_DEATH_MARK_SECONDS)
    markers.append([x, y, kind, int(seconds * FPS)])


def draw(screen, font):
    """Newest event at the bottom, older ones above it. Each line has a dark
    shadow for readability, is colored by its kind, and fades out during its
    last second."""
    y = screen.get_height() - 8 - FEED_LINE_HEIGHT * len(entries)
    if entries:
        # A see-through panel behind the lines, as wide as the longest one
        width = max(font.size(text)[0] for text, _, _ in entries) + 16
        panel = pygame.Surface((width, FEED_LINE_HEIGHT * len(entries) + 8), pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 14, 18, 150), panel.get_rect(), border_radius=6)
        screen.blit(panel, (4, y - 4))
    for text, frames_left, kind in entries:
        alpha = 255 if frames_left > FPS else int(255 * frames_left / FPS)  # 255 = fully visible
        shadow = font.render(text, True, FEED_SHADOW_COLOR)
        label = font.render(text, True, EVENT_COLORS.get(kind, FEED_TEXT_COLOR))
        shadow.set_alpha(alpha)
        label.set_alpha(alpha)
        screen.blit(shadow, (11, y + 1))
        screen.blit(label, (10, y))
        y += FEED_LINE_HEIGHT
