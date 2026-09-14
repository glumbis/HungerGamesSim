"""The start screen: see (and rename) the tributes before the Games begin."""
import pygame

from config import (
    FPS, NUM_PLAYERS, DEFAULT_NAMES, NAME_MAX_LENGTH, HUD_TEXT_COLOR,
    START_BACKGROUND, START_TITLE_COLOR, START_FIELD_COLOR, START_FIELD_ACTIVE_COLOR,
    START_BUTTON_COLOR,
)

ROW_HEIGHT = 38     # screen pixels per district row
FIELD_WIDTH = 220   # width of one name field


def layout(screen):
    """Where everything goes on the screen. Returns the left edge of the
    district labels, the top of the first row, one rectangle per name field
    (in player order: District 1 boy, District 1 girl, District 2 boy, ...)
    and the rectangle of the Start button."""
    width, _ = screen.get_size()  # _ = the height, not needed here
    left = width // 2 - 300
    top = 120
    fields = []
    for i in range(NUM_PLAYERS):
        # divmod(7, 2) gives (3, 1): player 7 is in district row 3, second of its pair
        row, column = divmod(i, 2)
        x = left + 130 + column * (FIELD_WIDTH + 20)
        y = top + row * ROW_HEIGHT
        fields.append(pygame.Rect(x, y, FIELD_WIDTH, ROW_HEIGHT - 8))
    button = pygame.Rect(0, 0, 240, 44)
    button.center = (width // 2, top + (NUM_PLAYERS // 2) * ROW_HEIGHT + 35)
    return left, top, fields, button


def finished(names):
    """The final names: an empty name falls back to its default.
    .strip() removes spaces at the ends, and an empty text counts as False."""
    return [name.strip() or default for name, default in zip(names, DEFAULT_NAMES)]


def run_start_screen(screen, clock, names=None):
    """Show the start screen until the Games are started. `names` are the
    names to start from (the previous game's, or the defaults if None).
    Returns the list of names, or None if the window was closed."""
    names = list(names or DEFAULT_NAMES)  # list(...) makes a copy we can change
    selected = None  # index of the name being edited, or None
    title_font = pygame.font.Font(None, 60)
    font = pygame.font.Font(None, 26)

    while True:
        left, top, fields, button = layout(screen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button.collidepoint(event.pos):
                    return finished(names)
                # Clicking a field selects it; clicking anywhere else deselects
                selected = None
                for i, rect in enumerate(fields):
                    if rect.collidepoint(event.pos):
                        selected = i
            elif event.type == pygame.KEYDOWN:
                if selected is None:
                    if event.key == pygame.K_RETURN:
                        return finished(names)
                elif event.key in (pygame.K_RETURN, pygame.K_TAB):
                    selected = (selected + 1) % NUM_PLAYERS  # on to the next field
                elif event.key == pygame.K_ESCAPE:
                    selected = None
                elif event.key == pygame.K_BACKSPACE:
                    names[selected] = names[selected][:-1]  # remove the last character
                elif event.unicode and event.unicode.isprintable() \
                        and len(names[selected]) < NAME_MAX_LENGTH:
                    names[selected] += event.unicode  # the character that was typed

        # --- Drawing ---
        center_x = screen.get_width() // 2
        screen.fill(START_BACKGROUND)
        title = title_font.render("The 74th Hunger Games", True, START_TITLE_COLOR)
        screen.blit(title, title.get_rect(center=(center_x, 42)))
        hint = font.render("Click a name to change it (Tab: next, Esc: done). "
                           "Enter or Start begins the Games.", True, HUD_TEXT_COLOR)
        screen.blit(hint, hint.get_rect(center=(center_x, 82)))

        for column, heading in enumerate(("Boy", "Girl")):
            label = font.render(heading, True, START_TITLE_COLOR)
            screen.blit(label, (left + 138 + column * (FIELD_WIDTH + 20), top - 24))
        for row in range(NUM_PLAYERS // 2):
            label = font.render(f"District {row + 1}", True, HUD_TEXT_COLOR)
            screen.blit(label, (left, top + row * ROW_HEIGHT + 7))

        for i, rect in enumerate(fields):
            color = START_FIELD_ACTIVE_COLOR if i == selected else START_FIELD_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=4)
            text = names[i] + ("|" if i == selected else "")  # | shows where you type
            screen.blit(font.render(text, True, HUD_TEXT_COLOR), (rect.x + 8, rect.y + 7))

        pygame.draw.rect(screen, START_BUTTON_COLOR, button, border_radius=6)
        label = font.render("Start the Games", True, (20, 20, 20))
        screen.blit(label, label.get_rect(center=button.center))

        pygame.display.flip()
        clock.tick(FPS)
