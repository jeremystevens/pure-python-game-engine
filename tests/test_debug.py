import io
import unittest
from unittest.mock import MagicMock

from engine.collision.collider import AABBCollider, CircleCollider, PointCollider
from engine.core.logger import LogLevel, get_logger, set_global_log_level
from engine.debug.overlay import DebugOverlay
from engine.math.vector2 import Vector2
from engine.scene.game_object import GameObject
from engine.scene.scene import Scene


class FakeInputManager:
    def __init__(self, pressed_keys=()):
        self.pressed_keys = set(pressed_keys)

    def is_key_just_pressed(self, key):
        return key in self.pressed_keys


class FakeEngine:
    def __init__(self, scene=None, target_fps=60):
        self.target_fps = target_fps
        self.current_scene = scene
        self.scene_manager = MagicMock(stack_depth=1)

    def get_fps(self):
        return 60.0


class DebugOverlayTests(unittest.TestCase):
    def setUp(self):
        # Log level is process-global; pin it so warning()/info() calls in
        # these tests are never silently suppressed by a prior test's state.
        set_global_log_level(LogLevel.DEBUG)
        self.logger = get_logger('Debug')
        self.output = io.StringIO()
        self.errors = io.StringIO()
        self.logger.set_output_stream(self.output)
        self.logger.set_error_stream(self.errors)
        self.logger.enable_colors(False)
        self.overlay = DebugOverlay(FakeEngine())

    def make_circle(self, scene, position, radius=5):
        game_object = GameObject('Circle')
        game_object.transform.position = position
        collider = game_object.add_component(CircleCollider(radius))
        scene.add_object(game_object)
        return game_object, collider

    def make_box(self, scene, position, size=Vector2(10, 10)):
        game_object = GameObject('Box')
        game_object.transform.position = position
        collider = game_object.add_component(AABBCollider(size))
        scene.add_object(game_object)
        return game_object, collider

    def test_defaults_are_hidden_and_at_info_level(self):
        self.assertFalse(self.overlay.stats_visible)
        self.assertFalse(self.overlay.colliders_visible)
        self.assertEqual(self.overlay.log_level, LogLevel.INFO)

    def test_f3_and_f4_toggle_independently(self):
        self.overlay.handle_input(FakeInputManager(['f3']))
        self.assertTrue(self.overlay.stats_visible)
        self.assertFalse(self.overlay.colliders_visible)

        self.overlay.handle_input(FakeInputManager(['f4']))
        self.assertTrue(self.overlay.stats_visible)
        self.assertTrue(self.overlay.colliders_visible)

        self.overlay.handle_input(FakeInputManager(['f3']))
        self.assertFalse(self.overlay.stats_visible)
        self.assertTrue(self.overlay.colliders_visible)

    def test_f5_cycles_through_every_log_level_and_wraps(self):
        expected_order = [LogLevel.WARNING, LogLevel.ERROR, LogLevel.DEBUG, LogLevel.INFO]
        for expected in expected_order:
            self.output.seek(0)
            self.output.truncate(0)
            self.errors.seek(0)
            self.errors.truncate(0)
            self.overlay.handle_input(FakeInputManager(['f5']))
            self.assertEqual(self.overlay.log_level, expected)
            combined_output = self.output.getvalue() + self.errors.getvalue()
            self.assertIn(f"Log level set to {expected.name}", combined_output)

    def test_f6_dumps_scene_and_returns_object_count(self):
        scene = Scene('Test Scene')
        self.make_circle(scene, Vector2(1, 2))
        self.make_box(scene, Vector2(3, 4))
        self.overlay.engine.current_scene = scene

        self.overlay.handle_input(FakeInputManager(['f6']))

        output = self.output.getvalue()
        self.assertIn("Test Scene", output)
        self.assertIn("2 object(s)", output)
        self.assertIn("'Circle'", output)
        self.assertIn("'Box'", output)

    def test_dump_scene_handles_no_active_scene(self):
        count = self.overlay.dump_scene(None)
        self.assertEqual(count, 0)
        self.assertIn("No active scene", self.output.getvalue())

    def test_record_frame_tracks_history_and_computes_stats(self):
        for seconds in (0.010, 0.020, 0.030):
            self.overlay.record_frame(seconds)

        average_ms, minimum_ms, maximum_ms = self.overlay.frame_time_stats_ms()
        self.assertAlmostEqual(average_ms, 20.0)
        self.assertAlmostEqual(minimum_ms, 10.0)
        self.assertAlmostEqual(maximum_ms, 30.0)

    def test_frame_time_stats_are_zero_with_no_history(self):
        self.assertEqual(self.overlay.frame_time_stats_ms(), (0.0, 0.0, 0.0))

    def test_record_frame_warns_only_when_slow(self):
        target = 1.0 / self.overlay.engine.target_fps

        self.overlay.record_frame(target)
        self.assertEqual(self.errors.getvalue(), "")

        self.overlay.record_frame(target * 3)
        self.assertIn("Slow frame", self.errors.getvalue())

    def test_history_is_bounded(self):
        for _ in range(DebugOverlay.FRAME_HISTORY_SIZE + 10):
            self.overlay.record_frame(0.016)
        self.assertEqual(len(self.overlay._frame_times_seconds), DebugOverlay.FRAME_HISTORY_SIZE)

    def test_collect_colliders_skips_inactive_and_destroyed_objects(self):
        scene = Scene()
        _, active_collider = self.make_circle(scene, Vector2.zero())
        inactive_object, _ = self.make_circle(scene, Vector2(1, 1))
        destroyed_object, _ = self.make_circle(scene, Vector2(2, 2))
        inactive_object.set_active(False)
        destroyed_object.destroy()

        colliders = self.overlay.collect_colliders(scene)

        self.assertEqual(colliders, [active_collider])

    def test_collect_colliders_returns_empty_list_for_no_scene(self):
        self.assertEqual(self.overlay.collect_colliders(None), [])

    def test_render_draws_nothing_when_both_flags_disabled(self):
        renderer = MagicMock()
        scene = Scene()
        self.make_circle(scene, Vector2.zero())

        self.overlay.render(renderer, scene)

        renderer.draw_circle.assert_not_called()
        renderer.draw_rectangle.assert_not_called()
        renderer.draw_text.assert_not_called()

    def test_render_draws_circle_and_box_collider_outlines(self):
        renderer = MagicMock()
        scene = Scene()
        self.make_circle(scene, Vector2(5, 5), radius=3)
        self.make_box(scene, Vector2(1, 1), size=Vector2(8, 4))
        self.overlay.colliders_visible = True

        self.overlay.render(renderer, scene)

        renderer.draw_circle.assert_called_once()
        renderer.draw_rectangle.assert_called_once()
        _, box_size_arg, *_ = renderer.draw_rectangle.call_args.args
        self.assertAlmostEqual(box_size_arg.x, 8)
        self.assertAlmostEqual(box_size_arg.y, 4)

    def test_render_draws_a_point_collider_with_a_minimum_visible_radius(self):
        renderer = MagicMock()
        scene = Scene()
        game_object = GameObject('Point')
        game_object.add_component(PointCollider())
        scene.add_object(game_object)
        self.overlay.colliders_visible = True

        self.overlay.render(renderer, scene)

        radius_arg = renderer.draw_circle.call_args.args[1]
        self.assertGreaterEqual(radius_arg, 1.0)

    def test_render_draws_five_stat_lines_when_enabled(self):
        renderer = MagicMock()
        scene = Scene('Test Scene')
        self.overlay.engine.current_scene = scene
        self.overlay.stats_visible = True

        self.overlay.render(renderer, scene)

        self.assertEqual(renderer.draw_text.call_count, 5)


if __name__ == '__main__':
    unittest.main()
