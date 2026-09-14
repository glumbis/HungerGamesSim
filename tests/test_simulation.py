"""Automatic tests: run whole Games without a window and check that the
rules hold. Run them all from the project folder with:

    python -m unittest

Each test plays one or more complete Games, so this takes a little while."""
import contextlib
import io
import os
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"          # no real window
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402  (imported after the settings above on purpose)

import config  # noqa: E402
import events  # noqa: E402
import main  # noqa: E402
import narration  # noqa: E402

MAX_SECONDS = 20 * 60  # a Games longer than this counts as stuck


def play_headless(seed, check=None):
    """Play one complete Games with the given seed. `check(sim)` is called
    after every step. Returns the finished Simulation."""
    events.reset()
    with contextlib.redirect_stdout(io.StringIO()):  # hide the printed fight log
        sim = main.Simulation(list(config.DEFAULT_NAMES), seed)
        frames = 0
        while not sim.game_over and frames < MAX_SECONDS * config.FPS:
            sim.step()
            frames += 1
            if check is not None:
                check(sim)
    return sim


class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    def test_games_finish_with_at_most_one_survivor(self):
        for seed in (1, 2):
            sim = play_headless(seed)
            self.assertTrue(sim.game_over, f"seed {seed} never finished")
            self.assertLessEqual(len(sim.players), 1)

    def test_loners_never_join_alliances(self):
        def check(sim):
            for player in sim.players:
                if player.loner:
                    self.assertIsNone(player.alliance, f"loner {player.name} joined an alliance")
        play_headless(3, check)

    def test_alliances_never_too_big(self):
        def check(sim):
            for player in sim.players:
                if player.alliance is not None:
                    self.assertLessEqual(len(player.alliance.members), config.ALLIANCE_MAX_SIZE)
        play_headless(4, check)

    def test_standings_are_complete(self):
        sim = play_headless(5)
        for player in sim.all_players:
            self.assertIsNotNone(player.placement, f"{player.name} has no place")

    def test_same_seed_same_winner(self):
        first = play_headless(6)
        second = play_headless(6)
        self.assertEqual([p.placement for p in first.all_players],
                         [p.placement for p in second.all_players])

    def test_every_narration_line_fills_in(self):
        names = dict(killer="K", victim="V", n=3, names="A and B", leader="L", others="B", newcomer="N",
                     traitor="T", loser="Lo", winner="W", a="A", b="B", kills=2, alliance="the Pack",
                     name="X", item="bread", area="northern forest", spot="water", day=2)
        for value in vars(narration).values():
            groups = value.values() if isinstance(value, dict) else [value]
            for group in groups:
                if isinstance(group, list) and group and isinstance(group[0], str):
                    for line in group:
                        line.format(**names)  # raises KeyError if a line uses an unknown name


if __name__ == "__main__":
    unittest.main()
