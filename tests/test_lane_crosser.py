import unittest

from engine.math.vector2 import Vector2
from engine.scene.scene import Scene
from engine.scene.scene_manager import SceneManager
from examples.games.lane_crosser import (
    AnimationClip,
    Car,
    Frog,
    GameOverScene,
    GameScene,
    GoalSlot,
    LaneCrosserGame,
    Log,
    RIVER_YS,
    START_POSITION,
    SpriteAtlas,
)


def make_atlas(size, *names):
    """A SpriteAtlas with no backing image -- exercises named-region and
    collision logic without needing a real loaded PNG."""
    atlas = SpriteAtlas(Vector2(*size), image=None)
    for index, name in enumerate(names):
        atlas.add_sprite(name, Vector2(index * 10, 0), Vector2(10, 10))
    return atlas


def make_frog():
    atlas = make_atlas((40, 10), 'idle', 'hop')
    clip = AnimationClip.from_frames('hop', ['hop'], frame_duration=0.15, loop=False)
    return Frog(atlas, clip)


def make_car(y, speed, sprite_name='red_right'):
    atlas = make_atlas((40, 10), 'red_right', 'red_left', 'blue_right', 'blue_left')
    return Car(atlas, sprite_name, y, speed)


def make_log(y, speed, phase=0.0):
    atlas = make_atlas((20, 10), 'bob_0', 'bob_1')
    clip = AnimationClip.from_frames('bob', ['bob_0', 'bob_1'], frame_duration=0.4, loop=True)
    return Log(atlas, clip, y, speed, phase=phase)


def make_goal(x):
    atlas = make_atlas((20, 10), 'empty', 'filled')
    return GoalSlot(atlas, x)


class FakeAssets:
    """Stands in for GameAssets without touching AssetManager or Tk."""

    def __init__(self):
        self.frog = make_atlas((40, 10), 'idle', 'hop')
        self.frog_hop_clip = AnimationClip.from_frames('hop', ['hop'], frame_duration=0.15, loop=False)
        self.cars = make_atlas((40, 10), 'red_right', 'red_left', 'blue_right', 'blue_left')
        self.logs = make_atlas((20, 10), 'bob_0', 'bob_1')
        self.log_bob_clip = AnimationClip.from_frames('bob', ['bob_0', 'bob_1'], frame_duration=0.4, loop=True)
        self.goals = make_atlas((20, 10), 'empty', 'filled')


class MechanicsTests(unittest.TestCase):
    """Direct GameObject-level tests using a bare Scene, no full engine."""

    def test_car_contact_kills_the_frog(self):
        scene = Scene()
        died = []
        scene.on_frog_died = lambda: died.append(True)

        frog = make_frog()
        frog.transform.position = Vector2(400, 400)
        scene.add_object(frog)

        car = make_car(400, 0)
        car.transform.position = Vector2(400, 400)
        scene.add_object(car)

        scene.update(0.016)

        self.assertEqual(died, [True])

    def test_riding_a_log_prevents_drowning_and_drifts_with_it(self):
        # A frog only ever enters a river row via hop(), called from inside
        # its own update() -- one frame before the trailing collision pass
        # that registers the log, and two frames before the next
        # death-check evaluates that settled state. Placing the frog
        # directly on a log with no prior settled frame would (correctly)
        # still drown it, since nothing has ever run collision detection
        # for that position yet -- so this test hops in, like a real player.
        scene = Scene()
        died = []
        scene.on_frog_died = lambda: died.append(True)

        river_y = RIVER_YS[0]
        log = make_log(river_y, speed=40)
        log.transform.position = Vector2(400, river_y)
        scene.add_object(log)

        frog = make_frog()
        frog.transform.position = Vector2(400, river_y + 50)  # one safe row below
        scene.add_object(frog)

        frog.hop(0, -50)  # lands exactly on the log, from a safe row
        scene.update(0.016)  # this frame's trailing collision pass registers it
        self.assertIs(frog.current_log, log)

        scene.update(0.016)  # settled frame: death-check now sees current_log
        self.assertEqual(died, [])

        start_x = frog.transform.position.x
        scene.update(0.2)
        self.assertGreater(frog.transform.position.x, start_x)

    def test_drowning_with_no_log_kills_the_frog(self):
        scene = Scene()
        died = []
        scene.on_frog_died = lambda: died.append(True)

        frog = make_frog()
        frog.transform.position = Vector2(400, RIVER_YS[0])
        scene.add_object(frog)

        scene.update(0.016)

        self.assertEqual(died, [True])

    def test_reaching_an_empty_goal_fills_it_and_notifies_the_scene(self):
        scene = Scene()
        filled_events = []
        scene.on_goal_filled = lambda: filled_events.append(True)

        goal = make_goal(400)
        scene.add_object(goal)

        frog = make_frog()
        frog.transform.position = Vector2(400, goal.transform.position.y)
        scene.add_object(frog)

        scene.update(0.016)

        self.assertTrue(goal.is_filled)
        self.assertEqual(filled_events, [True])

    def test_reaching_an_already_filled_goal_does_not_refill_it(self):
        scene = Scene()
        filled_events = []
        scene.on_goal_filled = lambda: filled_events.append(True)

        goal = make_goal(400)
        goal.is_filled = True
        scene.add_object(goal)

        frog = make_frog()
        frog.transform.position = Vector2(400, goal.transform.position.y)
        scene.add_object(frog)

        scene.update(0.016)

        self.assertEqual(filled_events, [])

    def test_car_wraps_around_the_screen(self):
        car = make_car(400, speed=1000)
        car.transform.position = Vector2(900, 400)
        car.update(0.016)
        self.assertLess(car.transform.position.x, 0)


class ProgressionTests(unittest.TestCase):
    """Level-up and persistent-progress behavior via a real GameScene, with
    the engine bootstrapped headlessly (no Tk window, no real image files)."""

    def create_game(self):
        game = object.__new__(LaneCrosserGame)
        game.assets = FakeAssets()
        game._last_scene = None
        scene = GameScene(1)
        game.scene_manager = SceneManager(game, scene)
        scene.initialize()
        return game, scene

    def test_filling_every_goal_advances_the_level_and_keeps_progress(self):
        game, scene = self.create_game()
        progress = scene.progress
        progress.score = 900
        progress.lives = 2

        for goal in scene.goal_slots:
            goal.is_filled = True
        scene.on_goal_filled()
        game.scene_manager.process_pending()

        new_scene = game.current_scene
        self.assertEqual(new_scene.name, 'Game')
        self.assertIsNot(new_scene, scene)
        new_progress = new_scene.find_object('PlayerProgress')

        self.assertIs(new_progress, progress)
        self.assertEqual(new_progress.level, 2)
        self.assertEqual(new_progress.score, 900 + 100 + 500)
        self.assertEqual(new_progress.lives, 2)
        self.assertIsNotNone(new_scene.find_object('Frog'))

    def test_filling_one_goal_does_not_advance_the_level(self):
        game, scene = self.create_game()
        scene.goal_slots[0].is_filled = True

        scene.on_goal_filled()
        game.scene_manager.process_pending()

        self.assertIs(game.current_scene, scene)
        self.assertEqual(scene.progress.level, 1)

    def test_losing_the_last_life_goes_to_game_over(self):
        game, scene = self.create_game()
        game.register_scene('game_over', GameOverScene)
        scene.progress.lives = 1

        scene.on_frog_died()
        game.scene_manager.process_pending()

        self.assertEqual(game.current_scene.name, 'GameOver')

    def test_losing_a_life_with_lives_remaining_just_respawns(self):
        game, scene = self.create_game()
        scene.progress.lives = 2
        scene.frog.transform.position = Vector2(999, 999)

        scene.on_frog_died()

        self.assertEqual(scene.progress.lives, 1)
        self.assertIs(game.current_scene, scene)
        self.assertEqual(scene.frog.transform.position, START_POSITION)


if __name__ == '__main__':
    unittest.main()
