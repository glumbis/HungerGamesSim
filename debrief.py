"""The debrief, shown when the Games are over: the winner, some numbers and
awards, a chart of how many tributes were alive over time, the final
standings, and a scrollable list of everything that happened. Click a
tribute in the standings to see only that tribute's story."""
from collections import Counter

import pygame

import alliances
import events
from config import (
    FPS, HUD_TEXT_COLOR, START_BACKGROUND, START_TITLE_COLOR, START_FIELD_COLOR,
    EVENT_COLORS, FIRE_COLOR,
)

ROW_HEIGHT = 17     # screen pixels per standings row
EVENT_ROW_HEIGHT = 18
CHART_HEIGHT = 110


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
    causes = {"mutts": "killed by mutts", "fire": "burned", "flood": "drowned", "arena": "caught by the arena"}
    return causes.get(player.cause_of_death, f"died of {player.cause_of_death}")


def stats_lines(sim):
    """A few numbers about the Games."""
    fallen = [player for player in sim.all_players if not player.alive]
    causes = Counter(player.cause_of_death for player in fallen)  # counts each cause
    gamemaker_deaths = causes["mutts"] + causes["fire"] + causes["flood"] + causes["arena"]
    return [
        f"Length: {clock_text(sim.frames_since_start)} ({sim.gamemakers.day} days)",
        f"Seed: {sim.seed}",
        f"Fights: {sim.arena.fights_started}",
        f"Fell in the bloodbath: {sim.bloodbath_deaths}",
        f"Killed in combat: {causes['combat']}",
        f"Hunger / thirst / sleep: {causes['hunger']} / {causes['thirst']} / {causes['sleep']}",
        f"Killed by the Gamemakers: {gamemaker_deaths}",
        f"Sponsor gifts: {events.counts['sponsor gifts']}",
        f"Alliances formed: {events.counts['alliances formed']}",
        f"Betrayals: {events.counts['betrayals']}",
    ]


def award_lines(sim):
    """Awards for memorable tributes (each only if someone earned it)."""
    everyone = sim.all_players
    awards = []
    top_killer = max(everyone, key=lambda player: player.kills)
    if top_killer.kills > 0:
        awards.append(f"Most kills: {top_killer.name} ({top_killer.kills})")
    peaceful = [player for player in everyone if player.kills == 0]
    if peaceful:
        # lowest placement number = lasted longest
        best = min(peaceful, key=lambda player: player.placement or 99)
        awards.append(f"Survived longest without a kill: {best.name} (place {best.placement})")
    gifted = max(everyone, key=lambda player: getattr(player, "gifts", 0))
    if getattr(gifted, "gifts", 0) > 0:
        awards.append(f"Sponsors' favorite: {gifted.name} ({gifted.gifts} gift(s))")
    traitor = max(everyone, key=lambda player: getattr(player, "betrayals", 0))
    if getattr(traitor, "betrayals", 0) > 0:
        awards.append(f"Biggest traitor: {traitor.name}")
    if alliances.records:
        name, size = max(alliances.records.items(), key=lambda item: item[1])
        awards.append(f"Biggest alliance: {name} ({size} members)")
    return awards


def draw_chart(screen, small, sim, rect):
    """Tributes alive over time as a line, with the bloodbath and the finale marked."""
    pygame.draw.rect(screen, START_FIELD_COLOR, rect, border_radius=6)
    screen.blit(small.render("Tributes alive over time", True, START_TITLE_COLOR), (rect.x + 8, rect.y + 5))
    history = sim.alive_history
    if len(history) < 2:
        return
    top = max(history)
    inner = rect.inflate(-24, -34)
    inner.y = rect.y + 24

    def point(second, alive):
        return (inner.x + inner.width * second / (len(history) - 1),
                inner.bottom - inner.height * alive / top)

    for frame, label in ((sim.bloodbath_end_frame, "bloodbath"), (sim.finale_frame, "finale")):
        if frame is not None:
            x = point(min(frame // FPS, len(history) - 1), 0)[0]
            pygame.draw.line(screen, FIRE_COLOR, (x, inner.y), (x, inner.bottom), 1)
            screen.blit(small.render(label, True, FIRE_COLOR), (x + 3, inner.y))
    pygame.draw.lines(screen, START_TITLE_COLOR, False,
                      [point(second, alive) for second, alive in enumerate(history)], 2)
    screen.blit(small.render(str(top), True, HUD_TEXT_COLOR), (rect.x + 4, inner.y - 6))
    screen.blit(small.render(clock_text(sim.frames_since_start), True, HUD_TEXT_COLOR),
                (inner.right - 30, rect.bottom - 16))


def run_debrief(screen, clock, sim):
    """Show the debrief until the viewer chooses what to do next.
    Returns "again" for new Games, "replay" for the same Games again, or "quit"."""
    title_font = pygame.font.Font(None, 46)
    font = pygame.font.Font(None, 22)
    small = pygame.font.Font(None, 19)
    winner = sim.players[0] if sim.players else None
    # Winner first, then by placement; players who fell together share a place
    standings = sorted(sim.all_players, key=lambda player: (player.placement, player.id))
    scroll = 0         # how many event lines are scrolled past
    focus = None       # the tribute whose story is shown (None = everything)
    row_rects = []     # clickable rectangles of the standings rows

    while True:
        width, height = screen.get_size()
        info = stats_lines(sim) + award_lines(sim)
        stats_rows = (len(info) + 1) // 2
        events_left = width // 2 + 20
        events_width = width - events_left - 20
        events_top = 90 + CHART_HEIGHT + 10

        # The events to show (only the focused tribute's, if one is chosen),
        # wrapped to fit, each line keeping the color of its event
        event_lines = []
        for text, kind in zip(events.history, events.history_kinds):
            if focus is not None and focus.name not in text:
                continue
            color = EVENT_COLORS.get(kind, HUD_TEXT_COLOR)
            event_lines += [(line, color) for line in wrap(text, small, events_width)]
        rows_shown = (height - events_top - 70) // EVENT_ROW_HEIGHT
        max_scroll = max(0, len(event_lines) - rows_shown)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEWHEEL:
                scroll -= event.y * 3  # wheel up (positive y) scrolls toward the start
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, player in row_rects:
                    if rect.collidepoint(event.pos):
                        focus = None if focus is player else player  # click again to show everything
                        scroll = 0
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "again"
                if event.key == pygame.K_r:
                    return "replay"
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
            subtitle = (f"District {winner.district}  -  {winner.temperament}, {winner.roaming}  -  "
                        f"{winner.kills} kill(s)")
        else:
            title = "The Games end with no victor"
            subtitle = "The last tributes fell at the same moment."
        label = title_font.render(title, True, START_TITLE_COLOR)
        screen.blit(label, label.get_rect(center=(center_x, 34)))
        label = font.render(subtitle, True, HUD_TEXT_COLOR)
        screen.blit(label, label.get_rect(center=(center_x, 66)))

        # Left: numbers and awards in two columns, then the standings table
        for i, line in enumerate(info):
            column, row = i % 2, i // 2  # even lines on the left, odd lines on the right
            screen.blit(small.render(line, True, HUD_TEXT_COLOR), (20 + column * 255, 92 + row * 19))

        table_top = 100 + stats_rows * 19
        columns = [("#", 20), ("Tribute", 45), ("Dist.", 165), ("Kills", 210), ("Fate", 255), ("Time", 440)]
        for heading, x in columns:
            screen.blit(small.render(heading, True, START_TITLE_COLOR), (x, table_top))
        row_rects = []
        row_height = min(ROW_HEIGHT, max(12, (height - table_top - 50) // len(standings)))
        for i, player in enumerate(standings):
            y = table_top + 18 + i * row_height
            rect = pygame.Rect(15, y - 1, events_left - 40, row_height)
            row_rects.append((rect, player))
            if player is focus:
                pygame.draw.rect(screen, START_FIELD_COLOR, rect)
            color = START_TITLE_COLOR if player.alive else HUD_TEXT_COLOR
            time = "-" if player.death_frame is None else clock_text(player.death_frame)
            cells = [str(player.placement), player.name, str(player.district),
                     str(player.kills), fate(player), time]
            for (_, x), text in zip(columns, cells):
                screen.blit(small.render(text, True, color), (x, y))

        # Right: the chart, then everything that happened
        draw_chart(screen, small, sim, pygame.Rect(events_left - 10, 90, events_width + 20, CHART_HEIGHT))
        pygame.draw.rect(screen, START_FIELD_COLOR,
                         (events_left - 10, events_top, events_width + 20, height - events_top - 40),
                         border_radius=6)
        heading = f"{focus.name}'s story" if focus else "What happened"
        screen.blit(font.render(heading, True, START_TITLE_COLOR), (events_left, events_top + 8))
        for i, (line, color) in enumerate(event_lines[scroll:scroll + rows_shown]):
            screen.blit(small.render(line, True, color), (events_left, events_top + 34 + i * EVENT_ROW_HEIGHT))
        if max_scroll > 0:
            position = f"{scroll + 1}-{min(scroll + rows_shown, len(event_lines))} of {len(event_lines)}"
            label = small.render(position, True, HUD_TEXT_COLOR)
            screen.blit(label, (events_left + events_width - label.get_width(), events_top + 10))

        hint = "Click a tribute: their story   Wheel: scroll   Enter: new Games   R: replay this seed   Esc: quit"
        label = small.render(hint, True, HUD_TEXT_COLOR)
        screen.blit(label, label.get_rect(center=(center_x, height - 18)))

        pygame.display.flip()
        clock.tick(FPS)
