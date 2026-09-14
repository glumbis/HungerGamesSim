"""The debrief, shown when the Games are over. It has three tabs, so nothing
has to share the screen:
- Summary: the winner, key numbers, awards and a chart of tributes alive
- Standings: every tribute's place, kills and fate (click one for its story)
- Story: everything that happened (or only the chosen tribute's events)"""
from collections import Counter

import pygame

import alliances
import events
import ui
from config import FPS, EVENT_COLORS, FIRE_COLOR

TABS = ["Summary", "Standings", "Story"]
ROW_HEIGHT = 22
EVENT_ROW_HEIGHT = 21


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


def stats(sim):
    """Key numbers about the Games, as (label, value) pairs."""
    fallen = [player for player in sim.all_players if not player.alive]
    causes = Counter(player.cause_of_death for player in fallen)  # counts each cause
    gamemakers = causes["mutts"] + causes["fire"] + causes["flood"] + causes["arena"]
    return [
        ("Length", f"{clock_text(sim.frames_since_start)}  ({sim.gamemakers.day} days)"),
        ("Fights", str(sim.arena.fights_started)),
        ("Bloodbath deaths", str(sim.bloodbath_deaths)),
        ("Killed in combat", str(causes["combat"])),
        ("Hunger / thirst / sleep", f"{causes['hunger']} / {causes['thirst']} / {causes['sleep']}"),
        ("Killed by Gamemakers", str(gamemakers)),
        ("Sponsor gifts", str(events.counts["sponsor gifts"])),
        ("Alliances / betrayals", f"{events.counts['alliances formed']} / {events.counts['betrayals']}"),
        ("Seed", str(sim.seed)),
    ]


def awards(sim):
    """Awards for memorable tributes, as (title, who) pairs (only if earned)."""
    everyone = sim.all_players
    result = []
    top_killer = max(everyone, key=lambda player: player.kills)
    if top_killer.kills > 0:
        result.append(("Most kills", f"{top_killer.name} ({top_killer.kills})"))
    peaceful = [player for player in everyone if player.kills == 0]
    if peaceful:
        best = min(peaceful, key=lambda player: player.placement or 99)  # lowest place = lasted longest
        result.append(("Survivor without a kill", f"{best.name} (place {best.placement})"))
    gifted = max(everyone, key=lambda player: player.gifts)
    if gifted.gifts > 0:
        gift_word = "gift" if gifted.gifts == 1 else "gifts"
        result.append(("Sponsors' favorite", f"{gifted.name} ({gifted.gifts} {gift_word})"))
    traitor = max(everyone, key=lambda player: player.betrayals)
    if traitor.betrayals > 0:
        result.append(("Biggest traitor", traitor.name))
    if alliances.records:
        name, size = max(alliances.records.items(), key=lambda item: item[1])
        result.append(("Biggest alliance", f"{name} ({size})"))
    return result


def draw_chart(screen, sim, rect):
    """Tributes alive over time as a line, with the bloodbath and finale marked."""
    ui.panel(screen, rect)
    ui.text(screen, "Tributes alive over time", ui.font(15, bold=True), ui.ACCENT, (rect.x + 14, rect.y + 10))
    history = sim.alive_history
    if len(history) < 2:
        return
    small = ui.font(12)
    top = max(history)
    inner = pygame.Rect(rect.x + 44, rect.y + 42, rect.width - 64, rect.height - 72)

    def point(second, alive):
        return (inner.x + inner.width * second / (len(history) - 1),
                inner.bottom - inner.height * alive / top)

    # Grid lines and labels every 6 tributes
    for alive in range(0, top + 1, 6):
        y = point(0, alive)[1]
        pygame.draw.line(screen, ui.PANEL_LIGHT, (inner.x, y), (inner.right, y), 1)
        ui.text(screen, str(alive), small, ui.MUTED, (inner.x - 8, y), "midright")
    for frame, label in ((sim.bloodbath_end_frame, "bloodbath over"), (sim.finale_frame, "finale")):
        if frame is not None:
            x = point(min(frame // FPS, len(history) - 1), 0)[0]
            pygame.draw.line(screen, FIRE_COLOR, (x, inner.y), (x, inner.bottom), 1)
            ui.text(screen, label, small, FIRE_COLOR, (x + 4, inner.y))
    pygame.draw.lines(screen, ui.ACCENT, False, [point(second, alive) for second, alive in enumerate(history)], 2)
    ui.text(screen, "0:00", small, ui.MUTED, (inner.x, inner.bottom + 6))
    ui.text(screen, clock_text(sim.frames_since_start), small, ui.MUTED, (inner.right, inner.bottom + 6), "topright")


def draw_summary(screen, sim, area):
    """Numbers and awards side by side on top, the chart below."""
    half = (area.width - 16) // 2
    numbers = pygame.Rect(area.x, area.y, half, 250)
    prizes = pygame.Rect(area.x + half + 16, area.y, half, 250)
    for box, title, rows in ((numbers, "The Games in numbers", stats(sim)), (prizes, "Awards", awards(sim))):
        ui.panel(screen, box)
        ui.text(screen, title, ui.font(15, bold=True), ui.ACCENT, (box.x + 14, box.y + 10))
        for i, (label, value) in enumerate(rows):
            y = box.y + 42 + i * 22
            ui.text(screen, label, ui.font(14), ui.MUTED, (box.x + 14, y))
            ui.text(screen, ui.fit(value, ui.font(14, bold=True), box.width // 2 - 10), ui.font(14, bold=True),
                    ui.TEXT, (box.right - 14, y), "topright")
    chart = pygame.Rect(area.x, area.y + 266, area.width, area.height - 266)
    draw_chart(screen, sim, chart)


def draw_standings(screen, standings, area, focus, mouse):
    """The standings table. Returns the clickable row rectangles."""
    ui.panel(screen, area)
    columns = [("#", 0.03), ("Tribute", 0.08), ("District", 0.30), ("Kills", 0.41), ("Fate", 0.50), ("Time", 0.90)]
    header_font, row_font = ui.font(13, bold=True), ui.font(14)
    for heading, share in columns:
        ui.text(screen, heading, header_font, ui.ACCENT, (area.x + area.width * share, area.y + 12))
    row_height = min(ROW_HEIGHT, (area.height - 44) // len(standings))
    rows = []
    for i, player in enumerate(standings):
        y = area.y + 36 + i * row_height
        rect = pygame.Rect(area.x + 6, y, area.width - 12, row_height)
        rows.append((rect, player))
        if player is focus:
            pygame.draw.rect(screen, ui.PANEL_HOVER, rect, border_radius=4)
        elif rect.collidepoint(mouse):
            pygame.draw.rect(screen, ui.PANEL_LIGHT, rect, border_radius=4)
        color = ui.ACCENT if player.alive else ui.TEXT
        time = "-" if player.death_frame is None else clock_text(player.death_frame)
        cells = [str(player.placement), player.name, str(player.district), str(player.kills), fate(player), time]
        for (_, share), text in zip(columns, cells):
            x = area.x + area.width * share
            ui.text(screen, ui.fit(text, row_font, area.width * 0.38), row_font, color, (x, rect.centery), "midleft")
    return rows


def run_debrief(screen, clock, sim):
    """Show the debrief until the viewer chooses what to do next.
    Returns "again" for new Games, "replay" for the same Games again, or "quit"."""
    winner = sim.players[0] if sim.players else None
    # Winner first, then by placement; players who fell together share a place
    standings = sorted(sim.all_players, key=lambda player: (player.placement, player.id))
    tab = 0          # which tab is open
    scroll = 0       # how many story lines are scrolled past
    focus = None     # the tribute whose story is shown (None = everything)
    rows = []        # clickable standings rows
    tab_rects = []

    while True:
        width, height = screen.get_size()
        mouse = pygame.mouse.get_pos()
        area = pygame.Rect(24, 150, width - 48, height - 150 - 56)

        # The story lines (only the focused tribute's, if one is chosen)
        story_font = ui.font(14)
        story = []
        for text, kind in zip(events.history, events.history_kinds):
            if focus is not None and focus.name not in text:
                continue
            color = EVENT_COLORS.get(kind, ui.TEXT)
            story += [(line, color) for line in wrap(text, story_font, area.width - 40)]
        rows_shown = (area.height - 56) // EVENT_ROW_HEIGHT
        max_scroll = max(0, len(story) - rows_shown)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEWHEEL:
                scroll -= event.y * 3  # wheel up (positive y) scrolls toward the start
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(tab_rects):
                    if rect.collidepoint(event.pos):
                        tab = i
                if TABS[tab] == "Standings":
                    for rect, player in rows:
                        if rect.collidepoint(event.pos):
                            focus, tab, scroll = player, TABS.index("Story"), 0
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "again"
                if event.key == pygame.K_r:
                    return "replay"
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    tab = event.key - pygame.K_1
                elif event.key == pygame.K_TAB:
                    tab = (tab + 1) % len(TABS)
                elif event.key == pygame.K_a:
                    focus, scroll = None, 0  # show everyone's story again
                elif event.key == pygame.K_UP:
                    scroll -= 1
                elif event.key == pygame.K_DOWN:
                    scroll += 1
                elif event.key == pygame.K_PAGEUP:
                    scroll -= rows_shown
                elif event.key == pygame.K_PAGEDOWN:
                    scroll += rows_shown
        scroll = max(0, min(scroll, max_scroll))

        # --- Drawing ---
        screen.fill(ui.BACKGROUND)
        center_x = width // 2
        if winner is not None:
            title = f"{winner.name} wins the Hunger Games"
            subtitle = f"District {winner.district}  -  {winner.temperament}, {winner.roaming}  -  {winner.kills} kill(s)"
        else:
            title, subtitle = "No victor", "The last tributes fell at the same moment."
        ui.text(screen, title, ui.font(30, bold=True), ui.ACCENT, (center_x, 44), "center")
        ui.text(screen, subtitle, ui.font(15), ui.MUTED, (center_x, 78), "center")

        # Tabs
        tab_rects = []
        for i, name in enumerate(TABS):
            rect = pygame.Rect(0, 0, 140, 34)
            rect.center = (center_x + (i - 1) * 150, 122)
            tab_rects.append(rect)
            ui.button(screen, rect, f"{i + 1}  {name}", ui.font(14, bold=True),
                      active=i == tab, hover=rect.collidepoint(mouse))

        if TABS[tab] == "Summary":
            draw_summary(screen, sim, area)
        elif TABS[tab] == "Standings":
            rows = draw_standings(screen, standings, area, focus, mouse)
        else:
            ui.panel(screen, area)
            heading = f"{focus.name}'s story   (A: show everyone)" if focus else "Everything that happened"
            ui.text(screen, heading, ui.font(15, bold=True), ui.ACCENT, (area.x + 16, area.y + 12))
            for i, (line, color) in enumerate(story[scroll:scroll + rows_shown]):
                ui.text(screen, line, story_font, color, (area.x + 20, area.y + 44 + i * EVENT_ROW_HEIGHT))
            if max_scroll > 0:
                position = f"{scroll + 1}-{min(scroll + rows_shown, len(story))} of {len(story)}"
                ui.text(screen, position, ui.font(13), ui.MUTED, (area.right - 16, area.y + 14), "topright")

        hint = "1/2/3 or Tab: switch tabs   Wheel: scroll   Enter: new Games   R: replay this seed   Esc: quit"
        ui.text(screen, hint, ui.font(13), ui.MUTED, (center_x, height - 26), "center")

        pygame.display.flip()
        clock.tick(FPS)
