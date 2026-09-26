import importlib
import unittest


EXAMPLE_MODULES = (
    'examples.games.asteroids_game',
    'examples.games.breakout_game',
    'examples.games.centipede_game',
    'examples.games.space_shooter',
    'examples.games.ui_game',
    'examples.demos.atlas',
    'examples.demos.basic_game',
    'examples.demos.ecs',
    'examples.demos.hot_reload',
    'examples.demos.input_profiles',
    'examples.demos.logging',
)


class ExampleImportTests(unittest.TestCase):
    def test_examples_import_without_starting_a_game_window(self):
        for module_name in EXAMPLE_MODULES:
            with self.subTest(module=module_name):
                importlib.import_module(module_name)


if __name__ == '__main__':
    unittest.main()
