"""The start screen: see the tributes before the Games begin, rename them,
and choose their traits. Every trait can be left on "random"."""
import pygame

import ui
from config import FPS, NUM_PLAYERS, DEFAULT_NAMES, NAME_MAX_LENGTH, PROFICIENCIES

# The choices for each setting; clicking a setting moves on to the next choice
OPTIONS = {
    "temperament": ["random", "killer", "balanced", "coward"],
    "roaming": ["random", "edge", "normal", "explorer"],
    "allies": ["auto", "never"],
    "proficiency": ["random"] + PROFICIENCIES,
}
HEADINGS = {"temperament": "Temperament", "roaming": "Roaming", "allies": "Allies", "proficiency": "Proficient"}
CHOICE_COLORS = {  # a colored tint for choices that stand out
    "killer": (120, 50, 46),
    "coward": (48, 70, 118),
    "never": (96, 70, 40),
}
ROW_HEIGHT = 34
COLUMN_WIDTH = 480
COLUMN_GAP = 14
NAME_WIDTH = 118
CHIP_WIDTH = 74


def default_settings():
    """Every tribute on random traits."""
    return [{"temperament": "random", "roaming": "random", "allies": "auto", "proficiency": "random"}
            for _ in range(NUM_PLAYERS)]


def layout(screen):
    """Where everything goes. Boys are in the left column and girls in the
    right, one row per district. Returns the name fields, the setting chips
    (each (rect, player index, setting)), the row rectangles and the buttons."""
    width, _ = screen.get_size()
    left = (width - (2 * COLUMN_WIDTH + COLUMN_GAP)) // 2
    top = 150
    fields, chips, rows = [], [], []
    for i in range(NUM_PLAYERS):
        district, column = divmod(i, 2)  # divmod(7, 2) = (3, 1): district row 3, girl
        x = left + column * (COLUMN_WIDTH + COLUMN_GAP)
        y = top + district * ROW_HEIGHT
        rows.append(pygame.Rect(x, y, COLUMN_WIDTH, ROW_HEIGHT - 4))
        fields.append(pygame.Rect(x + 40, y + 3, NAME_WIDTH, ROW_HEIGHT - 10))
        for k, setting in enumerate(OPTIONS):
            chip = pygame.Rect(x + 40 + NAME_WIDTH + 8 + k * (CHIP_WIDTH + 4), y + 3, CHIP_WIDTH, ROW_HEIGHT - 10)
            chips.append((chip, i, setting))
    bottom = top + (NUM_PLAYERS // 2) * ROW_HEIGHT + 16
    start = pygame.Rect(0, 0, 220, 42)
    start.midtop = (width // 2 + 120, bottom)
    reset = pygame.Rect(0, 0, 220, 42)
    reset.midtop = (width // 2 - 120, bottom)
    return left, top, fields, chips, rows, start, reset


def finished(names, settings):
    """The final names (an empty name falls back to its default) and settings."""
    names = [name.strip() or default for name, default in zip(names, DEFAULT_NAMES)]
    return names, settings


def run_start_screen(screen, clock, names=None, settings=None):
    """Show the start screen until the Games are started. `names` and
    `settings` are what to start from (the previous game's, or the defaults).
    Returns (names, settings), or None if the window was closed."""
    names = list(names or DEFAULT_NAMES)  # list(...) makes a copy we can change
    # Copies, filled up with defaults for any option missing from older settings
    settings = [{**default, **choice} for default, choice in zip(default_settings(), settings or default_settings())]
    selected = None  # index of the name being edited, or None

    while True:
        left, top, fields, chips, rows, start, reset = layout(screen)
        mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
                if event.button == 1 and start.collidepoint(event.pos):
                    return finished(names, settings)
                if event.button == 1 and reset.collidepoint(event.pos):
                    settings = default_settings()
                selected = None
                for i, rect in enumerate(fields):
                    if rect.collidepoint(event.pos):
                        selected = i
                for rect, i, setting in chips:
                    if rect.collidepoint(event.pos):
                        # Left click: next choice; right click: previous choice
                        choices = OPTIONS[setting]
                        step = 1 if event.button == 1 else -1
                        position = choices.index(settings[i][setting])
                        settings[i][setting] = choices[(position + step) % len(choices)]
            elif event.type == pygame.KEYDOWN:
                if selected is None:
                    if event.key == pygame.K_RETURN:
                        return finished(names, settings)
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
        width = screen.get_width()
        screen.fill(ui.BACKGROUND)
        ui.text(screen, "THE 74TH HUNGER GAMES", ui.font(34, bold=True), ui.ACCENT, (width // 2, 44), "center")
        ui.text(screen, "Name your tributes and choose their traits, or leave them to chance.",
                ui.font(16), ui.MUTED, (width // 2, 82), "center")
        ui.text(screen, "Click a name to type  -  click a trait to change it (right click: back)  -  Enter: start",
                ui.font(13), ui.MUTED, (width // 2, 104), "center")

        small = ui.font(13)
        for column, heading in enumerate(("Boys", "Girls")):
            x = left + column * (COLUMN_WIDTH + COLUMN_GAP)
            ui.text(screen, heading, ui.font(15, bold=True), ui.ACCENT, (x + 40, top - 22))
            for k, setting in enumerate(OPTIONS):
                chip_x = x + 40 + NAME_WIDTH + 8 + k * (CHIP_WIDTH + 4)
                ui.text(screen, HEADINGS[setting], ui.font(12), ui.MUTED, (chip_x + CHIP_WIDTH // 2, top - 14), "center")

        for i, row in enumerate(rows):
            ui.panel(screen, row, ui.PANEL, None, radius=6)
            ui.text(screen, f"D{i // 2 + 1}", ui.font(14, bold=True), ui.MUTED, (row.x + 10, row.centery), "midleft")

        for i, rect in enumerate(fields):
            active = i == selected
            pygame.draw.rect(screen, ui.PANEL_HOVER if active else ui.PANEL_LIGHT, rect, border_radius=5)
            if active:
                pygame.draw.rect(screen, ui.ACCENT, rect, 1, border_radius=5)
            label = names[i] + ("|" if active else "")  # | shows where you type
            ui.text(screen, ui.fit(label, ui.font(15), rect.width - 12), ui.font(15), ui.TEXT,
                    (rect.x + 8, rect.centery), "midleft")

        for rect, i, setting in chips:
            value = settings[i][setting]
            color = CHOICE_COLORS.get(value)
            hover = rect.collidepoint(mouse)
            ui.button(screen, rect, value, small, hover=hover, color=color)

        ui.button(screen, reset, "All traits random", ui.font(16), hover=reset.collidepoint(mouse))
        ui.button(screen, start, "Start the Games", ui.font(16, bold=True), active=True)

        pygame.display.flip()
        clock.tick(FPS)
