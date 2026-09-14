"""The shared look of the screens and overlays: colors, fonts, panels,
buttons and text. Keeping these in one place makes everything match."""
import pygame

# Colors (R, G, B)
BACKGROUND = (17, 19, 23)
PANEL = (29, 32, 39)
PANEL_LIGHT = (43, 47, 57)
PANEL_HOVER = (56, 61, 73)
BORDER = (62, 68, 82)
TEXT = (228, 230, 234)
MUTED = (148, 154, 166)
ACCENT = (234, 186, 78)       # gold, the Capitol's color
ACCENT_TEXT = (32, 26, 12)    # dark text on gold
RED = (226, 96, 86)
GREEN = (122, 200, 132)
BLUE = (118, 160, 238)

_fonts = {}  # fonts made so far, so each size is only created once


def font(size, bold=False):
    """A clean system font (Segoe UI on Windows) in the given size, or
    pygame's built-in font if none of those is installed."""
    key = (size, bold)
    if key not in _fonts:
        try:
            chosen = pygame.font.SysFont("segoeui,helvetica,arial", size, bold=bold)
        except Exception:  # some systems have no usable font list
            chosen = pygame.font.Font(None, int(size * 1.35))
        _fonts[key] = chosen
    return _fonts[key]


def text(screen, string, text_font, color, position, anchor="topleft", shadow=False):
    """Draw text with one of its corners (or its center) at `position`, e.g.
    anchor="center". Returns the rectangle it covers."""
    label = text_font.render(string, True, color)
    rect = label.get_rect(**{anchor: position})  # ** turns the dict into a keyword argument
    if shadow:
        screen.blit(text_font.render(string, True, (0, 0, 0)), rect.move(1, 1))
    screen.blit(label, rect)
    return rect


def fit(string, text_font, width):
    """Shorten `string` with "..." until it fits within `width` pixels."""
    if text_font.size(string)[0] <= width:
        return string
    while string and text_font.size(string + "...")[0] > width:
        string = string[:-1]
    return string + "..."


def panel(screen, rect, color=PANEL, border=BORDER, radius=8, alpha=None):
    """A rounded box. With `alpha` (0-255) it is see-through."""
    if alpha is None:
        pygame.draw.rect(screen, color, rect, border_radius=radius)
    else:
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)  # SRCALPHA: supports see-through pixels
        pygame.draw.rect(surface, color + (alpha,), surface.get_rect(), border_radius=radius)
        screen.blit(surface, rect.topleft)
    if border is not None:
        pygame.draw.rect(screen, border, rect, 1, border_radius=radius)


def button(screen, rect, label, text_font, active=False, hover=False, color=None):
    """A rounded button. `active` buttons are gold; `color` overrides the fill."""
    if active:
        fill, text_color = ACCENT, ACCENT_TEXT
    else:
        fill, text_color = (PANEL_HOVER if hover else PANEL_LIGHT), TEXT
    if color is not None:
        fill = color
    pygame.draw.rect(screen, fill, rect, border_radius=6)
    text(screen, fit(label, text_font, rect.width - 8), text_font, text_color, rect.center, "center")
