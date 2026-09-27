import unittest

from engine.math.vector2 import Vector2
from engine.scene.game_object import GameObject
from engine.scene.scene import Scene
from engine.scene.scene_manager import SceneManager


class RecordingObject(GameObject):
    def __init__(self, name, log, action=None):
        super().__init__(name)
        self.log = log
        self.action = action
        self.start_count = 0
        self.update_count = 0

    def on_start(self):
        self.start_count += 1
        self.log.append(f'{self.name}.start')

    def update(self, delta_time):
        self.update_count += 1
        self.log.append(f'{self.name}.update')
        if self.action:
            action = self.action
            self.action = None
            action()
        super().update(delta_time)

    def render(self, renderer):
        self.log.append(f'{self.name}.render')
        super().render(renderer)


class RecordingScene(Scene):
    def __init__(self, name, log):
        super().__init__(name)
        self.log = log

    def on_initialize(self):
        self.log.append(f'{self.name}.initialize')

    def on_pause(self):
        self.log.append(f'{self.name}.pause')

    def on_resume(self):
        self.log.append(f'{self.name}.resume')

    def on_cleanup(self):
        self.log.append(f'{self.name}.cleanup')

    def update(self, delta_time):
        self.log.append(f'{self.name}.update')
        super().update(delta_time)

    def render(self, renderer):
        self.log.append(f'{self.name}.render')
        super().render(renderer)


class SceneLifecycleTests(unittest.TestCase):
    def test_initialization_and_cleanup_are_idempotent(self):
        log = []
        scene = RecordingScene('scene', log)
        game_object = RecordingObject('object', log)
        scene.add_object(game_object)

        self.assertTrue(scene.initialize())
        self.assertFalse(scene.initialize())
        self.assertEqual(game_object.start_count, 1)

        self.assertTrue(scene.cleanup())
        self.assertFalse(scene.cleanup())
        self.assertEqual(log.count('scene.initialize'), 1)
        self.assertEqual(log.count('scene.cleanup'), 1)
        self.assertTrue(game_object.is_destroyed)

    def test_pause_blocks_update_but_allows_render(self):
        log = []
        scene = RecordingScene('scene', log)
        game_object = RecordingObject('object', log)
        scene.add_object(game_object)
        scene.initialize()

        self.assertTrue(scene.pause())
        self.assertFalse(scene.pause())
        scene.update(0.1)
        scene.render(object())

        self.assertEqual(game_object.update_count, 0)
        self.assertIn('object.render', log)
        self.assertTrue(scene.resume())
        self.assertFalse(scene.resume())
        scene.update(0.1)
        self.assertEqual(game_object.update_count, 1)

    def test_update_defers_addition_and_removal_to_synchronization_point(self):
        log = []
        scene = RecordingScene('scene', log)
        added = RecordingObject('added', log)
        removed = RecordingObject('removed', log)

        def mutate_scene():
            scene.add_object(added)
            scene.remove_object(removed)

        mutator = RecordingObject('mutator', log, mutate_scene)
        scene.add_object(mutator)
        scene.add_object(removed)
        scene.initialize()

        scene.update(0.1)

        self.assertEqual(removed.update_count, 0)
        self.assertEqual(added.update_count, 0)
        self.assertEqual(added.start_count, 1)
        self.assertIs(added.scene, scene)
        self.assertIsNone(removed.scene)
        self.assertIs(scene.find_object('added'), added)
        self.assertIsNone(scene.find_object('removed'))

        scene.update(0.1)
        self.assertEqual(added.update_count, 1)

    def test_duplicate_names_restore_previous_index_when_latest_is_removed(self):
        scene = Scene()
        first = GameObject('duplicate')
        second = GameObject('duplicate')
        scene.add_object(first)
        scene.add_object(second)
        self.assertIs(scene.find_object('duplicate'), second)

        scene.remove_object(second)

        self.assertIs(scene.find_object('duplicate'), first)

    def test_objects_cannot_belong_to_two_scenes(self):
        first = Scene('first')
        second = Scene('second')
        game_object = GameObject('shared')
        first.add_object(game_object)

        with self.assertRaisesRegex(ValueError, 'another scene'):
            second.add_object(game_object)


class SceneManagerTests(unittest.TestCase):
    def test_registry_rejects_duplicates_and_unknown_names(self):
        manager = SceneManager()
        manager.register('menu', Scene('Menu'))

        with self.assertRaisesRegex(ValueError, 'already registered'):
            manager.register('menu', Scene('Other'))
        with self.assertRaisesRegex(KeyError, 'missing'):
            manager.replace_now('missing')

        self.assertEqual(manager.registered_scene_names, ('menu',))
        self.assertTrue(manager.unregister('menu'))
        self.assertFalse(manager.unregister('menu'))

    def test_factories_create_fresh_scenes_for_repeated_names(self):
        created = []

        def factory():
            scene = Scene(f'Scene {len(created)}')
            created.append(scene)
            return scene

        manager = SceneManager()
        manager.register('level', factory)
        first = manager.replace_now('level')
        second = manager.replace_now('level')

        self.assertIsNot(first, second)
        self.assertEqual(created, [first, second])
        self.assertTrue(first.game_objects == [])

    def test_push_updates_only_top_and_renders_bottom_to_top(self):
        log = []
        base = RecordingScene('base', log)
        overlay = RecordingScene('overlay', log)
        base.add_object(RecordingObject('base_object', log))
        overlay.add_object(RecordingObject('overlay_object', log))
        manager = SceneManager(initial_scene=base)
        manager.initialize_current()

        manager.push_now(overlay)
        manager.update(0.1)
        manager.render(object())

        self.assertTrue(base.is_paused)
        self.assertEqual(manager.current_scene, overlay)
        self.assertEqual(manager.stack_depth, 2)
        self.assertNotIn('base_object.update', log)
        self.assertIn('overlay_object.update', log)
        self.assertLess(log.index('base.render'), log.index('overlay.render'))

    def test_pop_cleans_overlay_and_resumes_scene_below(self):
        log = []
        base = RecordingScene('base', log)
        overlay = RecordingScene('overlay', log)
        manager = SceneManager(initial_scene=base)
        manager.initialize_current()
        manager.push_now(overlay)

        removed = manager.pop_now()

        self.assertIs(removed, overlay)
        self.assertIs(manager.current_scene, base)
        self.assertFalse(base.is_paused)
        self.assertIn('overlay.cleanup', log)
        self.assertIn('base.resume', log)
        self.assertIsNone(manager.pop_now())

    def test_queued_transitions_wait_for_explicit_processing(self):
        base = Scene('base')
        overlay = Scene('overlay')
        manager = SceneManager(initial_scene=base)
        manager.initialize_current()

        manager.push(overlay)

        self.assertIs(manager.current_scene, base)
        self.assertTrue(manager.has_pending_transition)
        manager.process_pending()
        self.assertIs(manager.current_scene, overlay)
        self.assertFalse(manager.has_pending_transition)

    def test_replace_transfers_persistent_objects_without_restarting(self):
        log = []
        old = RecordingScene('old', log)
        new = RecordingScene('new', log)
        persistent = RecordingObject('persistent', log)
        persistent.set_persistent()
        disposable = RecordingObject('disposable', log)
        old.add_object(persistent)
        old.add_object(disposable)
        manager = SceneManager(initial_scene=old)
        manager.initialize_current()

        manager.replace_now(new)

        self.assertIs(manager.current_scene, new)
        self.assertIs(persistent.scene, new)
        self.assertFalse(persistent.is_destroyed)
        self.assertEqual(persistent.start_count, 1)
        self.assertTrue(disposable.is_destroyed)
        self.assertLess(log.index('old.cleanup'), log.index('new.initialize'))

    def test_persistent_name_conflict_leaves_source_scene_unchanged(self):
        old = Scene('old')
        persistent = GameObject('player')
        persistent.set_persistent()
        old.add_object(persistent)
        old.initialize()
        new = Scene('new')
        new.add_object(GameObject('player'))
        manager = SceneManager(initial_scene=old)

        with self.assertRaisesRegex(ValueError, 'conflicts'):
            manager.replace_now(new)

        self.assertIs(manager.current_scene, old)
        self.assertIs(persistent.scene, old)
        self.assertFalse(persistent.is_destroyed)

    def test_clear_cleans_stack_from_top_to_bottom(self):
        log = []
        base = RecordingScene('base', log)
        overlay = RecordingScene('overlay', log)
        manager = SceneManager(initial_scene=base)
        manager.initialize_current()
        manager.push_now(overlay)
        log.clear()

        manager.clear()

        self.assertEqual(manager.stack_depth, 0)
        self.assertLess(log.index('overlay.cleanup'), log.index('base.cleanup'))

    def test_manager_attaches_engine_reference(self):
        engine = object()
        scene = Scene('scene')
        manager = SceneManager(engine=engine)

        manager.replace_now(scene)

        self.assertIs(scene.engine, engine)


if __name__ == '__main__':
    unittest.main()
