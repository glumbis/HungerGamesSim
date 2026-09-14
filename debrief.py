"""The debrief, shown when the Games are over: the winner, some numbers, the
final standings and a scrollable list of everything that happened."""
from collections import Counter

import pygame

import events
from config import FPS, HUD_TEXT_COLOR, START_BACKGROUND, START_TITLE_COLOR, START_FIELD_COLOR

ROW_HEIGHT = 17     # screen pixels per standings row
EVENT_ROW_HEIGHT = 18


def clock_text(frames):
    """Frames as minutes:seconds, e.g. 3:07."""
    minutes, seconds = divmod(frames // FPS, 60)
    return f"{minutes}:{seconds:02d}"


def wrap(text, font, width):
    """Split `text` into lines that each fit within `width` pixels."""
    lines, line = [], ""
    for word in text.split(" "):
        attempt = word if not line else line + " " + word
        if font.size(attempt)[0] <= width:  # font.size gives (width, height) of the text
            line = attempt
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fate(player):
    """How a tribute's Games ended, in a few words."""
    if player.alive:
        return "Victor"
    if player.cause_of_death == "combat":
        return f"killed by {player.killer_name}"
    return f"died of {player.cause_of_death}"


def stats_lines(sim):
    """A few numbers about the Games."""
    fallen = [player for player in sim.all_players if not player.alive]
    causes = Counter(player.cause_of_death for player in fallen)  # counts each cause
    top_killer = max(sim.all_players, key=lambda player: player.kills)
    return [
        f"Length: {clock_text(sim.frames_since_start)}",
        f"Fights: {sim.arena.fights_started}",
        f"Fell in the bloodbath: {sim.bloodbath_deaths}",
        f"Killed in combat: {causes['combat']}",
        f"Hunger / thirst / sleep: {causes['hunger']} / {causes['thirst']} / {causes['sleep']}",
        f"Alliances formed: {events.counts['alliances formed']}",
        f"Betrayals: {events.counts['betrayals']}",
        f"Most kills: {top_killer.name} ({top_killer.kills})",
    ]


def run_debrief(screen, clock, sim):
    """Show the debrief until the viewer chooses what to do next.
    Returns "again" for new Games, or "quit"."""
    title_font = pygame.font.Font(None, 46)
    font = pygame.font.Font(None, 22)
    small = pygame.font.Font(None, 19)
    winner = sim.players[0] if sim.players else None
    # Winner first, then by placement; players who fell together share a place
    standings = sorted(sim.all_players, key=lambda player: (player.placement, player.id))
    scroll = 0  # how many event lines are scrolled past

    while True:
        width, height = screen.get_size()
        events_left = width // 2 + 20
        events_width = width - events_left - 20
        event_lines = []
        for text in events.history:
            event_lines += wrap(text, small, events_width)
        rows_shown = (height - 170) // EVENT_ROW_HEIGHT
        max_scroll = max(0, len(event_lines) - rows_shown)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEWHEEL:
                scroll -= event.y * 3  # wheel up (positive y) scrolls toward the start
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "again"
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key == pygame.K_UP:
                    scroll -= 1
                elif event.key == pygame.K_DOWN:
                    scroll += 1
                elif event.key == pygame.K_PAGEUP:
                    scroll -= rows_shown
                elif event.key == pygame.K_PAGEDOWN:
                    scroll += rows_shown
        scroll = max(0, min(scroll, max_scroll))

        # --- Drawing ---
        screen.fill(START_BACKGROUND)
        center_x = width // 2
        if winner is not None:
            title = f"{winner.name} wins the Hunger Games!"
            subtitle = (f"District {winner.id // 2 + 1}  -  {winner.temperament}, {winner.roaming}  -  "
                        f"{winner.kills} kill(s)")
        else:
            title = "The Games end with no victor"
            subtitle = "The last tributes fell at the same moment."
        label = title_font.render(title, True, START_TITLE_COLOR)
        screen.blit(label, label.get_rect(center=(center_x, 34)))
        label = font.render(subtitle, True, HUD_TEXT_COLOR)
        screen.blit(label, label.get_rect(center=(center_x, 66)))

        # Left: numbers in two columns, then the standings table
        for i, line in enumerate(stats_lines(sim)):
            column, row = i % 2, i // 2  # even lines on the left, odd lines on the right
            screen.blit(font.render(line, True, HUD_TEXT_COLOR), (20 + column * 250, 95 + row * 22))

        table_top = 195
        columns = [("#", 20), ("Tribute", 45), ("Dist.", 165), ("Kills", 210), ("Fate", 255), ("Time", 455)]
        for heading, x in columns:
            screen.blit(small.render(heading, True, START_TITLE_COLOR), (x, table_top))
        for i, player in enumerate(standings):
            y = table_top + 20 + i * ROW_HEIGHT
            color = START_TITLE_COLOR if player.alive else HUD_TEXT_COLOR
            time = "-" if player.death_frame is None else clock_text(player.death_frame)
            cells = [str(player.placement), player.name, str(player.id // 2 + 1),
                     str(player.kills), fate(player), time]
            for (_, x), text in zip(columns, cells):
                screen.blit(small.render(text, True, color), (x, y))

        # Right: everything that happened
        pygame.draw.rect(screen, START_FIELD_COLOR,
                         (events_left - 10, 90, events_width + 20, height - 130), border_radius=6)
        screen.blit(font.render("What happened", True, START_TITLE_COLOR), (events_left, 98))
        for i, line in enumerate(event_lines[scroll:scroll + rows_shown]):
            screen.blit(small.render(line, True, HUD_TEXT_COLOR),
                        (events_left, 124 + i * EVENT_ROW_HEIGHT))
        if max_scroll > 0:
            position = f"{scroll + 1}-{min(scroll + rows_shown, len(event_lines))} of {len(event_lines)}"
            label = small.render(position, True, HUD_TEXT_COLOR)
            screen.blit(label, (events_left + events_width - label.get_width(), 100))

        hint = "Mouse wheel / Up / Down: scroll events     Enter: new Games     Esc: quit"
        label = font.render(hint, True, HUD_TEXT_COLOR)
        screen.blit(label, label.get_rect(center=(center_x, height - 20)))

        pygame.display.flip()
        clock.tick(FPS)
