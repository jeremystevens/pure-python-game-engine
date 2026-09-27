import tkinter as tk
import unittest
from unittest.mock import ANY, patch

from engine.core.engine import GameEngine
from engine.core.window import Window
from engine.scene.scene import Scene


class FakeRoot:
    def __init__(self):
        self.update_error = None

    def title(self, title):
        pass

    def geometry(self, geometry):
        pass

    def resizable(self, width, height):
        pass

    def protocol(self, name, callback):
        pass

    def focus_set(self):
        pass

    def bind(self, event, callback):
        pass

    def update_idletasks(self):
        if self.update_error:
            raise self.update_error

    def update(self):
        if self.update_error:
            raise self.update_error

    def attributes(self, name, value):
        pass

    def quit(self):
        pass

    def destroy(self):
        pass


class FakeCanvas:
    def __init__(self, root, **kwargs):
        pass

    def pack(self):
        pass

    def bind(self, event, callback):
        pass

    def delete(self, target):
        pass

    def configure(self, **kwargs):
        pass


class WindowTests(unittest.TestCase):
    def create_window(self, target_fps=60, max_delta_time=0.1):
        root = FakeRoot()
        with (
            patch('engine.core.window.tk.Tk', return_value=root),
            patch('engine.core.window.Canvas', FakeCanvas),
            patch('engine.core.window.time.perf_counter', return_value=10.0),
        ):
            window = Window('Test', (320, 240), target_fps, max_delta_time)
        return window, root

    def test_target_fps_and_delta_limit_are_configurable(self):
        window, _ = self.create_window(target_fps=30, max_delta_time=0.05)

        self.assertEqual(window.target_fps, 30)
        self.assertAlmostEqual(window.frame_time, 1 / 30)
        self.assertEqual(window.max_delta_time, 0.05)
        self.assertAlmostEqual(window.delta_time, 1 / 30)

    def test_invalid_timing_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            Window(target_fps=0)
        with self.assertRaises(ValueError):
            Window(max_delta_time=0)

    def test_update_uses_monotonic_time_limits_rate_and_bounds_delta(self):
        window, _ = self.create_window(target_fps=10, max_delta_time=0.05)

        with (
            patch(
                'engine.core.window.time.perf_counter',
                side_effect=[10.01, 10.1],
            ),
            patch('engine.core.window.time.sleep') as sleep,
        ):
            window.update()

        sleep.assert_called_once_with(ANY)
        self.assertAlmostEqual(sleep.call_args.args[0], 0.09)
        self.assertAlmostEqual(window.raw_delta_time, 0.1)
        self.assertEqual(window.delta_time, 0.05)

    def test_tcl_error_marks_window_for_closure(self):
        window, root = self.create_window()
        root.update_error = tk.TclError('window closed')

        with patch(
            'engine.core.window.time.perf_counter',
            side_effect=[10.0, 10.01],
        ):
            window.update()

        self.assertTrue(window.should_close())


class FakeWindow:
    def __init__(self, log, delta_time=0.02):
        self.log = log
        self.delta_time = delta_time
        self.raw_delta_time = delta_time
        self.actual_fps = 50.0
        self.canvas = object()
        self.closed = False

    def set_key_press_callback(self, callback):
        pass

    def set_key_release_callback(self, callback):
        pass

    def set_mouse_callback(self, callback):
        pass

    def should_close(self):
        return self.closed

    def clear(self):
        self.log.append('window.clear')

    def update(self):
        self.log.append('window.update')

    def quit(self):
        self.log.append('window.quit')

    def toggle_fullscreen(self):
        pass

    def set_vsync(self, enabled):
        pass


class FakeAssetManager:
    def __init__(self, log):
        self.log = log

    def clear(self):
        self.log.append('assets.clear')


class FakeInputManager:
    def __init__(self, log):
        self.log = log

    def on_key_press(self, keysym, keycode):
        pass

    def on_key_release(self, keysym, keycode):
        pass

    def on_mouse_event(self, event_type, button, x, y):
        pass

    def is_key_just_pressed(self, key):
        return False

    def update(self):
        self.log.append('input.update')


class FakeScene(Scene):
    def __init__(self, name, log):
        super().__init__(name)
        self.log = log

    def initialize(self):
        self.log.append(f'{self.name}.initialize')

    def update(self, delta_time):
        self.log.append(f'{self.name}.update')

    def render(self, renderer):
        self.log.append(f'{self.name}.render')

    def cleanup(self):
        self.log.append(f'{self.name}.cleanup')


class RecordingEngine(GameEngine):
    def __init__(self, log, fail_during_update=False):
        self.log = log
        self.fail_during_update = fail_during_update
        super().__init__('Test Engine', (320, 240), 50, 0.05)

    def initialize(self):
        self.log.append('game.initialize')

    def update(self, delta_time):
        self.log.append('game.update')
        if self.fail_during_update:
            raise RuntimeError('update failed')
        self.quit()

    def render(self):
        self.log.append('game.render')

    def cleanup(self):
        self.log.append('game.cleanup')


class GameEngineLifecycleTests(unittest.TestCase):
    def create_engine(self, log, fail_during_update=False):
        window = FakeWindow(log)
        inputs = FakeInputManager(log)
        assets = FakeAssetManager(log)
        with (
            patch('engine.core.engine.Window', return_value=window) as window_class,
            patch('engine.core.engine.InputManager', return_value=inputs),
            patch('engine.core.engine.Renderer', return_value=object()),
            patch('engine.core.engine.AssetManager', return_value=assets),
        ):
            engine = RecordingEngine(log, fail_during_update)
        return engine, window, window_class

    def test_constructor_forwards_timing_configuration_to_window(self):
        engine, _, window_class = self.create_engine([])

        window_class.assert_called_once_with('Test Engine', (320, 240), 50, 0.05)
        self.assertEqual(engine.target_fps, 50)
        self.assertEqual(engine.max_delta_time, 0.05)

    def test_constructor_configures_central_asset_manager(self):
        log = []
        window = FakeWindow(log)
        assets = FakeAssetManager(log)
        with (
            patch('engine.core.engine.Window', return_value=window),
            patch(
                'engine.core.engine.InputManager',
                return_value=FakeInputManager(log),
            ),
            patch('engine.core.engine.Renderer', return_value=object()),
            patch(
                'engine.core.engine.AssetManager',
                return_value=assets,
            ) as asset_manager_class,
        ):
            engine = GameEngine(asset_root='game-assets')

        asset_manager_class.assert_called_once_with('game-assets')
        self.assertIs(engine.asset_manager, assets)

    def test_run_has_predictable_lifecycle_order(self):
        log = []
        engine, _, _ = self.create_engine(log)
        engine.current_scene = FakeScene('scene', log)

        engine.run()

        self.assertEqual(
            log,
            [
                'game.initialize',
                'scene.initialize',
                'input.update',
                'scene.update',
                'game.update',
                'window.clear',
                'scene.render',
                'game.render',
                'window.update',
                'game.cleanup',
                'scene.cleanup',
                'assets.clear',
                'window.quit',
            ],
        )
        self.assertAlmostEqual(engine.delta_time, 0.02)
        self.assertAlmostEqual(engine.total_time, 0.02)
        self.assertFalse(engine.is_running)

    def test_current_scene_survives_shutdown_for_post_run_inspection(self):
        log = []
        engine, _, _ = self.create_engine(log)
        scene = FakeScene('scene', log)
        engine.current_scene = scene

        engine.run()

        self.assertIs(engine.current_scene, scene)
        self.assertEqual(engine.scene_manager.stack_depth, 0)

    def test_cleanup_runs_when_initialize_raises(self):
        log = []
        engine, _, _ = self.create_engine(log)
        engine.current_scene = FakeScene('scene', log)

        def initialize():
            log.append('game.initialize')
            raise RuntimeError('initialization failed')

        engine.initialize = initialize

        with self.assertRaisesRegex(RuntimeError, 'initialization failed'):
            engine.run()

        self.assertEqual(
            log,
            [
                'game.initialize',
                'game.cleanup',
                'scene.cleanup',
                'assets.clear',
                'window.quit',
            ],
        )
        self.assertFalse(engine.is_running)

    def test_cleanup_runs_when_game_update_raises(self):
        log = []
        engine, _, _ = self.create_engine(log, fail_during_update=True)
        engine.current_scene = FakeScene('scene', log)

        with self.assertRaisesRegex(RuntimeError, 'update failed'):
            engine.run()

        self.assertEqual(
            log[-4:],
            ['game.cleanup', 'scene.cleanup', 'assets.clear', 'window.quit'],
        )
        self.assertFalse(engine.is_running)

    def test_scene_transition_cleans_old_scene_before_initializing_new_scene(self):
        log = []
        engine, window, _ = self.create_engine(log)
        old_scene = FakeScene('old', log)
        new_scene = FakeScene('new', log)
        engine.current_scene = old_scene
        updates = 0

        def update(delta_time):
            nonlocal updates
            log.append('game.update')
            updates += 1
            if updates == 1:
                engine.load_scene(new_scene)
            else:
                engine.quit()

        engine.update = update
        engine.run()

        self.assertLess(log.index('old.cleanup'), log.index('new.initialize'))
        self.assertIn('new.update', log)
        self.assertIs(engine.current_scene, new_scene)
        self.assertEqual(log.count('old.cleanup'), 1)
        self.assertEqual(log.count('new.cleanup'), 1)
        self.assertEqual(log[-1], 'window.quit')


if __name__ == '__main__':
    unittest.main()
