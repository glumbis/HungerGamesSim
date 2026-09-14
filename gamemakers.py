"""The Gamemakers and the Capitol: everything that happens to the tributes
from outside. Day and night, sponsor gifts, fires and floods, mutts, the
shrinking arena near the end, and the feast. main.Simulation calls update()
every step and draw() every frame."""
import math
import random

import pygame

import ai
import events
import narration
from arena import LootItem
from config import (
    FPS, WORLD_WIDTH, WORLD_HEIGHT, VISION_RADIUS,
    DAY_SECONDS, NIGHT_SHARE, NIGHT_DARKNESS, FALLEN_SHOW_SECONDS,
    SPONSOR_CHECK_SECONDS, SPONSOR_BASE_CHANCE, PARACHUTE_FALL_SECONDS, PARACHUTE_COLOR,
    GAMEMAKER_EVENT_SECONDS, FIRE_RADIUS, FIRE_SECONDS, FIRE_DAMAGE_CHANCE, FIRE_COLOR, FLOOD_COLOR,
    MUTT_COUNT, MUTT_SECONDS, MUTT_SPEED, MUTT_KILL_CHANCE, MUTT_COLOR,
    SHRINK_START_PLAYERS, SHRINK_MIN_RADIUS, SHRINK_SECONDS, SHRINK_COLOR,
    FEAST_PLAYERS, FEAST_ITEMS, FEAST_DELAY_SECONDS, SHOWDOWN_PLAYERS,
    INJURY_SECONDS, DEATH_MARK_COLOR, HEART_COLOR, LOOT_CENTER_SPREAD,
    NEED_MAX, CARRY_LIMITS,
)
from utils import distance, angle_to

ITEM_NAMES = {"food": "bread", "water": "a flask of water", "weapon": "a weapon"}


def area_name(arena, x, y):
    """A rough description of where (x, y) is, e.g. "northern forest"."""
    vertical = "northern" if y < WORLD_HEIGHT / 3 else "southern" if y > 2 * WORLD_HEIGHT / 3 else ""
    horizontal = "western" if x < WORLD_WIDTH / 3 else "eastern" if x > 2 * WORLD_WIDTH / 3 else ""
    direction = vertical or horizontal or "central"
    return f"{direction} {arena.terrain_at(x, y)}"


class Mutt:
    """A beast released by the Gamemakers. It runs at the nearest tribute."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.frames_left = MUTT_SECONDS * FPS

    def update(self, players):
        self.frames_left -= 1
        prey = min(players, default=None, key=lambda player: distance(self.x, self.y, player.x, player.y))
        if prey is None:
            return None
        angle = angle_to(self.x, self.y, prey.x, prey.y)
        self.x += math.cos(angle) * MUTT_SPEED
        self.y += math.sin(angle) * MUTT_SPEED
        if distance(self.x, self.y, prey.x, prey.y) < 6 and prey.fight is None:
            return prey  # caught someone
        return None


class Gamemakers:
    def __init__(self, arena):
        self.arena = arena
        self.day = 1
        self.night = False
        self.fallen_today = []      # names of the tributes who fell since the last nightfall
        self.fallen_shown = []      # names shown in the sky right now
        self.fallen_frames = 0      # frames left showing them
        self.sponsor_timer = SPONSOR_CHECK_SECONDS * FPS
        self.event_timer = random.uniform(*GAMEMAKER_EVENT_SECONDS) * FPS
        self.hazards = []           # fires and floods, each [x, y, kind, frames_left]
        self.mutts = []
        self.parachutes = []        # falling gifts, each [receiver, kind, frames_left]
        self.shrink_frames = None   # frames since the arena started shrinking (None = not yet)
        self.feast_timer = None     # frames until the feast supplies appear (None = not announced)
        self.feast_done = False
        self.full_radius = math.hypot(WORLD_WIDTH, WORLD_HEIGHT) / 2

    # --- Every step --------------------------------------------------------

    def update(self, sim):
        players = sim.players
        self.update_day_night(sim)
        if not sim.opening_over or len(players) <= 1:
            return
        self.update_sponsors(players)
        self.update_hazards(players)
        self.update_mutts(players)
        self.update_shrink(players)
        self.update_feast(players)
        if len(players) > SHOWDOWN_PLAYERS:
            self.event_timer -= 1
            if self.event_timer <= 0:
                self.start_event(players)
                self.event_timer = random.uniform(*GAMEMAKER_EVENT_SECONDS) * FPS

    def update_day_night(self, sim):
        day_frames = DAY_SECONDS * FPS
        phase = (sim.frames_since_start % day_frames) / day_frames  # 0 at dawn, 1 at the next dawn
        night = phase >= 1 - NIGHT_SHARE
        if night and not self.night:
            # Nightfall: the anthem, and the faces of the fallen in the sky
            if self.fallen_today:
                events.log(narration.pick(narration.NIGHTFALL, day=self.day), "gamemaker")
            else:
                events.log(narration.pick(narration.NIGHTFALL_NONE, day=self.day), "gamemaker")
            self.fallen_shown = self.fallen_today
            self.fallen_today = []
            self.fallen_frames = FALLEN_SHOW_SECONDS * FPS
        elif not night and self.night:
            self.day += 1
            for player in sim.players:
                player.days_survived += 1
            events.log(narration.pick(narration.DAWN, day=self.day), "gamemaker")
        self.night = night
        ai.night = night
        if self.fallen_frames > 0:
            self.fallen_frames -= 1

    def darkness(self, sim):
        """How dark the night overlay is right now (0-255), fading in and out."""
        day_frames = DAY_SECONDS * FPS
        phase = (sim.frames_since_start % day_frames) / day_frames
        night_start = 1 - NIGHT_SHARE
        if phase < night_start:
            return 0
        into = (phase - night_start) / NIGHT_SHARE  # 0 at dusk, 1 at dawn
        return int(NIGHT_DARKNESS * min(1.0, 4 * min(into, 1 - into)))  # quick fade in and out

    # --- Sponsors ----------------------------------------------------------

    def update_sponsors(self, players):
        for parachute in list(self.parachutes):
            parachute[2] -= 1
            receiver, kind, frames_left = parachute
            if frames_left <= 0:
                self.parachutes.remove(parachute)
                if receiver.alive:
                    if receiver.can_carry(kind):
                        receiver.pick_up(kind)
                    else:
                        self.arena.loot.append(LootItem(kind, receiver.x, receiver.y))

        self.sponsor_timer -= 1
        if self.sponsor_timer > 0:
            return
        self.sponsor_timer = SPONSOR_CHECK_SECONDS * FPS

        # Sponsors favor tributes who put on a show: kills, big alliances, District 1's charm
        def appeal(player):
            score = 1 + player.kills + (len(player.alliance.members) / 2 if player.alliance else 0)
            return score * (2 if player.skill == "luxury" else 1)

        candidates = [player for player in players if self.wanted_gift(player)]
        if not candidates or random.random() > SPONSOR_BASE_CHANCE:
            return
        receiver = random.choices(candidates, weights=[appeal(player) for player in candidates])[0]
        kind = self.wanted_gift(receiver)
        self.parachutes.append([receiver, kind, int(PARACHUTE_FALL_SECONDS * FPS)])
        events.counts["sponsor gifts"] += 1
        receiver.gifts = getattr(receiver, "gifts", 0) + 1
        events.log(narration.pick(narration.SPONSOR_GIFT, name=receiver.name,
                                  item=ITEM_NAMES[kind]), "sponsor")

    def wanted_gift(self, player):
        """What a struggling tribute needs most, or None if it is doing fine."""
        if player.needs["thirst"] < 35 and player.inventory["water"] == 0:
            return "water"
        if player.needs["hunger"] < 35 and player.inventory["food"] == 0:
            return "food"
        if player.inventory["weapon"] == 0 and player.kills > 0:
            return "weapon"
        return None

    # --- Fires, floods and mutts --------------------------------------------

    def start_event(self, players):
        """Pick a Gamemaker event near a random tribute, to stir things up."""
        target = random.choice(players)
        x = max(FIRE_RADIUS / 2, min(target.x + random.uniform(-100, 100), WORLD_WIDTH - FIRE_RADIUS / 2))
        y = max(FIRE_RADIUS / 2, min(target.y + random.uniform(-100, 100), WORLD_HEIGHT - FIRE_RADIUS / 2))
        area = area_name(self.arena, x, y)
        kind = random.choice(["fire", "flood", "mutts"])
        events.counts["gamemaker events"] += 1
        if kind == "mutts":
            count = random.randint(*MUTT_COUNT)
            for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                self.mutts.append(Mutt(x + math.cos(angle) * 150, y + math.sin(angle) * 150))
            events.log(narration.pick(narration.MUTTS, n=count, area=area), "gamemaker")
        else:
            self.hazards.append([x, y, kind, FIRE_SECONDS * FPS])
            lines = narration.FIRE if kind == "fire" else narration.FLOOD
            events.log(narration.pick(lines, area=area), "gamemaker")

    def update_hazards(self, players):
        for hazard in self.hazards:
            hazard[3] -= 1
        self.hazards = [hazard for hazard in self.hazards if hazard[3] > 0]
        for x, y, kind, _ in self.hazards:
            for player in players:
                if player.alive and distance(player.x, player.y, x, y) < FIRE_RADIUS and \
                        random.random() < FIRE_DAMAGE_CHANCE:
                    player.alive = False
                    player.cause_of_death = kind

    def update_mutts(self, players):
        for mutt in list(self.mutts):
            caught = mutt.update([player for player in players if player.alive])
            if caught is not None:
                self.mutts.remove(mutt)  # a mutt attacks once
                if random.random() < MUTT_KILL_CHANCE:
                    caught.alive = False
                    caught.cause_of_death = "mutts"
                else:
                    caught.injury_timer = INJURY_SECONDS * FPS
                    events.log(narration.pick(narration.MUTT_ESCAPE, victim=caught.name), "gamemaker")
            elif mutt.frames_left <= 0:
                self.mutts.remove(mutt)

    # --- The end: shrinking arena and feast ---------------------------------

    def safe_radius(self):
        """How far from the cornucopia it is safe to be (the whole arena, until it shrinks)."""
        if self.shrink_frames is None:
            return self.full_radius
        share = min(1.0, self.shrink_frames / (SHRINK_SECONDS * FPS))
        return self.full_radius + (SHRINK_MIN_RADIUS - self.full_radius) * share

    def update_shrink(self, players):
        if self.shrink_frames is None:
            if len(players) <= SHRINK_START_PLAYERS:
                self.shrink_frames = 0
                events.log(narration.pick(narration.SHRINK), "gamemaker")
            return
        self.shrink_frames += 1
        radius = self.safe_radius()
        for player in players:
            outside = distance(player.x, player.y, self.arena.center_x, self.arena.center_y) - radius
            if outside > 0 and random.random() < 0.002 * min(outside / 50, 3):
                player.alive = False
                player.cause_of_death = "arena"

    def update_feast(self, players):
        if self.feast_done:
            return
        if self.feast_timer is None:
            if len(players) <= FEAST_PLAYERS:
                self.feast_timer = FEAST_DELAY_SECONDS * FPS
                events.log(narration.pick(narration.FEAST_ANNOUNCED), "gamemaker")
                ai.send_to_middle(players, self.arena, share=0.4)
            return
        self.feast_timer -= 1
        if self.feast_timer <= 0:
            self.feast_done = True
            for kind, count in FEAST_ITEMS.items():
                for _ in range(count):
                    x, y = self.arena.random_point_near_cornucopia()
                    self.arena.loot.append(LootItem(kind, x, y))
            events.log(narration.pick(narration.FEAST_READY), "gamemaker")

    # --- What the AI asks ----------------------------------------------------

    def escape_point(self, player):
        """A point to run to if the player is in danger (fire, flood, a mutt
        close by, or outside the shrinking arena), or None if it is safe."""
        for x, y, kind, _ in self.hazards:
            gap = distance(player.x, player.y, x, y)
            if gap < FIRE_RADIUS + 30:
                angle = angle_to(x, y, player.x, player.y)
                return (x + math.cos(angle) * (FIRE_RADIUS + 80), y + math.sin(angle) * (FIRE_RADIUS + 80))
        for mutt in self.mutts:
            if distance(player.x, player.y, mutt.x, mutt.y) < VISION_RADIUS * 1.5:
                angle = angle_to(mutt.x, mutt.y, player.x, player.y)
                return (player.x + math.cos(angle) * 150, player.y + math.sin(angle) * 150)
        radius = self.safe_radius()
        center_x, center_y = self.arena.center_x, self.arena.center_y
        if distance(player.x, player.y, center_x, center_y) > radius - 40:
            angle = angle_to(player.x, player.y, center_x, center_y)
            inward = min(150, distance(player.x, player.y, center_x, center_y))
            return (player.x + math.cos(angle) * inward, player.y + math.sin(angle) * inward)
        return None

    # --- Drawing -------------------------------------------------------------

    def draw(self, screen, camera):
        """Hazards, mutts, parachutes, the shrinking boundary and markers."""
        for x, y, kind, frames_left in self.hazards:
            radius = camera.size(FIRE_RADIUS, 4)
            color = FIRE_COLOR if kind == "fire" else FLOOD_COLOR
            flicker = 70 + int(25 * math.sin(frames_left * 0.2))
            overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)  # SRCALPHA: see-through
            pygame.draw.circle(overlay, color + (flicker,), (radius, radius), radius)
            center = camera.world_to_screen(x, y, screen)
            screen.blit(overlay, (center[0] - radius, center[1] - radius))

        if self.shrink_frames is not None:
            center = camera.world_to_screen(self.arena.center_x, self.arena.center_y, screen)
            pygame.draw.circle(screen, SHRINK_COLOR, center, camera.size(self.safe_radius(), 4), 3)

        for mutt in self.mutts:
            point = camera.world_to_screen(mutt.x, mutt.y, screen)
            pygame.draw.circle(screen, MUTT_COLOR, point, camera.size(4, 3))
            pygame.draw.circle(screen, FIRE_COLOR, point, camera.size(4, 3), 1)

        for receiver, _, frames_left in self.parachutes:
            # The parachute floats down onto the receiver from above
            height = frames_left / (PARACHUTE_FALL_SECONDS * FPS) * 60
            x, y = camera.world_to_screen(receiver.x, receiver.y - height, screen)
            size = camera.size(5, 4)
            pygame.draw.arc(screen, PARACHUTE_COLOR, (x - size, y - size, 2 * size, 2 * size), 0, math.pi, 2)
            pygame.draw.line(screen, PARACHUTE_COLOR, (x - size, y), (x, y + size), 1)
            pygame.draw.line(screen, PARACHUTE_COLOR, (x + size, y), (x, y + size), 1)

        for x, y, kind, _ in events.markers:
            point = camera.world_to_screen(x, y, screen)
            size = camera.size(3, 2)
            if kind == "death":
                # a small cross where a tribute fell
                pygame.draw.line(screen, DEATH_MARK_COLOR, (point[0] - size, point[1] - size),
                                 (point[0] + size, point[1] + size), 2)
                pygame.draw.line(screen, DEATH_MARK_COLOR, (point[0] + size, point[1] - size),
                                 (point[0] - size, point[1] + size), 2)

    def draw_fallen(self, screen, font):
        """At nightfall: the names of the day's fallen, in the sky (top middle)."""
        if self.fallen_frames <= 0 or not self.fallen_shown:
            return
        alpha = 255 if self.fallen_frames > FPS else int(255 * self.fallen_frames / FPS)
        lines = [f"The fallen of day {self.day}"] + self.fallen_shown
        for i, line in enumerate(lines):
            label = font.render(line, True, (240, 230, 200) if i == 0 else (220, 220, 230))
            label.set_alpha(alpha)
            screen.blit(label, label.get_rect(center=(screen.get_width() // 2, 70 + i * 20)))
