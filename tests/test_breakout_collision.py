import unittest
from unittest.mock import patch

from engine.math.vector2 import Vector2
from engine.scene.scene import Scene
from engine.scene.scene_manager import SceneManager
from examples.games.breakout_game import Ball, BreakoutGame, Brick, Paddle


class RecordingSoundGenerator:
    def __init__(self):
        self.played = []

    def play_sound(self, name):
        self.played.append(name)


class BreakoutCollisionIntegrationTests(unittest.TestCase):
    def setUp(self):
        print_patcher = patch('builtins.print')
        print_patcher.start()
        self.addCleanup(print_patcher.stop)

    def create_game(self):
        game = object.__new__(BreakoutGame)
        game.game_state = 'playing'
        game.score = 0
        game.bricks = []
        game.paddle = None
        game.sound_generator = RecordingSoundGenerator()
        scene = Scene('Breakout Test')
        game.scene_manager = SceneManager(game, scene)
        return game

    def test_ball_uses_engine_collision_to_bounce_from_paddle(self):
        game = self.create_game()
        game.ball = Ball()
        game.paddle = Paddle()
        game.ball.transform.position = Vector2(400, 545)
        game.ball.velocity = Vector2(0, 200)
        game.current_scene.add_object(game.ball)
        game.current_scene.add_object(game.paddle)

        game.current_scene.collision_system.update()

        self.assertLess(game.ball.velocity.y, 0)
        self.assertEqual(game.sound_generator.played, ['paddle_hit'])
        self.assertTrue(game.ball.collision_resolved)

    def test_ball_uses_engine_collision_to_destroy_and_score_brick(self):
        game = self.create_game()
        game.ball = Ball()
        game.ball.transform.position = Vector2(100, 80)
        game.ball.velocity = Vector2(0, -200)
        brick = Brick('#FF0000', 7, 100, 80)
        game.bricks = [brick]
        game.current_scene.add_object(game.ball)
        game.current_scene.add_object(brick)

        game.current_scene.collision_system.update()

        self.assertEqual(game.score, 7)
        self.assertEqual(game.bricks, [])
        self.assertTrue(brick.is_destroyed)
        self.assertNotIn(brick, game.current_scene.game_objects)
        self.assertGreater(game.ball.velocity.y, 0)
        self.assertAlmostEqual(game.ball.velocity.magnitude, 204)
        self.assertEqual(game.sound_generator.played, ['high_brick'])

    def test_ball_resolves_only_one_brick_when_contacts_overlap(self):
        game = self.create_game()
        game.ball = Ball()
        game.ball.transform.position = Vector2(100, 80)
        first = Brick('#FFFF00', 5, 100, 80)
        second = Brick('#0000FF', 3, 100, 80)
        game.bricks = [first, second]
        game.current_scene.add_object(game.ball)
        game.current_scene.add_object(first)
        game.current_scene.add_object(second)

        game.current_scene.collision_system.update()

        self.assertEqual(len(game.bricks), 1)
        self.assertEqual(game.score, 5)
        self.assertEqual(game.sound_generator.played, ['mid_brick'])


if __name__ == '__main__':
    unittest.main()
