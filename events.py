"""The event feed: key moments (eliminations, alliance news, the winner)
shown in the bottom-left corner of the screen and printed to the terminal."""
from config import (
    FPS,
    FEED_MAX_LINES, FEED_SECONDS, FEED_LINE_HEIGHT, FEED_TEXT_COLOR, FEED_SHADOW_COLOR,
)

entries = []     # events on screen, oldest first; each is [text, frames_left]
history = []     # every event of the current game, oldest first (for the debrief)
frame_count = 0  # frames since the start, used for the timestamps


def reset():
    """Forget everything, ready for a new game."""
    global frame_count  # see update() for what `global` does
    entries.clear()
    history.clear()
    frame_count = 0


def log(text):
    """Record an event: print it, add it to the on-screen feed and keep it
    in the history."""
    minutes, seconds = divmod(frame_count // FPS, 60)  # divmod gives (whole minutes, leftover seconds)
    stamped = f"{minutes}:{seconds:02d}  {text}"         # :02d pads to two digits, e.g. 1:05
    print(stamped)
    history.append(stamped)
    entries.append([stamped, FEED_SECONDS * FPS])
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


def draw(screen, font):
    """Newest event at the bottom, older ones above it. Each line has a dark
    shadow for readability and fades out during its last second."""
    y = screen.get_height() - 8 - FEED_LINE_HEIGHT * len(entries)
    for text, frames_left in entries:
        alpha = 255 if frames_left > FPS else int(255 * frames_left / FPS)  # 255 = fully visible
        shadow = font.render(text, True, FEED_SHADOW_COLOR)
        label = font.render(text, True, FEED_TEXT_COLOR)
        shadow.set_alpha(alpha)
        label.set_alpha(alpha)
        screen.blit(shadow, (11, y + 1))
        screen.blit(label, (10, y))
        y += FEED_LINE_HEIGHT
