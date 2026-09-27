import unittest

from engine.scene.game_object import Component, GameObject
from engine.scene.scene import Scene


class RecordingComponent(Component):
    def __init__(self):
        super().__init__()
        self.start_count = 0
        self.updates = []
        self.renderers = []
        self.destroy_count = 0

    def start(self):
        self.start_count += 1

    def update(self, delta_time):
        self.updates.append(delta_time)

    def render(self, renderer):
        self.renderers.append(renderer)

    def destroy(self):
        self.destroy_count += 1


class OtherRecordingComponent(RecordingComponent):
    pass


class RecordingGameObject(GameObject):
    def __init__(self, name, render_log=None):
        super().__init__(name)
        self.render_log = render_log

    def render(self, renderer):
        if self.render_log is not None:
            self.render_log.append(self.name)
        super().render(renderer)


class SpecializedGameObject(GameObject):
    pass


class GameObjectTests(unittest.TestCase):
    def test_component_add_lookup_and_remove(self):
        game_object = GameObject('Player')
        component = RecordingComponent()

        returned = game_object.add_component(component)

        self.assertIs(returned, component)
        self.assertIs(component.game_object, game_object)
        self.assertIs(game_object.get_component(RecordingComponent), component)
        self.assertTrue(game_object.has_component(RecordingComponent))
        self.assertTrue(game_object.remove_component(RecordingComponent))
        self.assertEqual(component.destroy_count, 1)
        self.assertIsNone(component.game_object)
        self.assertFalse(game_object.remove_component(RecordingComponent))

    def test_adding_same_component_type_replaces_existing_component(self):
        game_object = GameObject()
        first = game_object.add_component(RecordingComponent())
        second = game_object.add_component(RecordingComponent())

        self.assertEqual(first.destroy_count, 1)
        self.assertIsNone(first.game_object)
        self.assertIs(game_object.get_component(RecordingComponent), second)
        self.assertEqual(game_object.components_list, [second])

    def test_components_start_with_object_and_late_components_start_immediately(self):
        scene = Scene()
        game_object = GameObject()
        scene.add_object(game_object)

        initial = game_object.add_component(RecordingComponent())
        self.assertEqual(initial.start_count, 0)

        scene.initialize()
        late = game_object.add_component(OtherRecordingComponent())

        self.assertEqual(initial.start_count, 1)
        self.assertEqual(late.start_count, 1)

    def test_object_start_update_and_render_delegate_to_active_components(self):
        game_object = GameObject()
        active = game_object.add_component(RecordingComponent())
        inactive = game_object.add_component(OtherRecordingComponent())
        inactive.is_active = False
        renderer = object()

        game_object.start()
        game_object.update(0.25)
        game_object.render(renderer)

        self.assertEqual(active.start_count, 1)
        self.assertEqual(inactive.start_count, 1)
        self.assertEqual(active.updates, [0.25])
        self.assertEqual(active.renderers, [renderer])
        self.assertEqual(inactive.updates, [])
        self.assertEqual(inactive.renderers, [])

    def test_inactive_or_destroyed_object_does_not_update_or_render(self):
        game_object = GameObject()
        component = game_object.add_component(RecordingComponent())

        game_object.set_active(False)
        game_object.update(0.1)
        game_object.render(object())
        game_object.set_active(True)
        game_object.destroy()
        game_object.update(0.1)
        game_object.render(object())

        self.assertEqual(component.updates, [])
        self.assertEqual(component.renderers, [])

    def test_destroy_is_idempotent_and_destroys_all_components(self):
        game_object = GameObject()
        first = game_object.add_component(RecordingComponent())
        second = game_object.add_component(OtherRecordingComponent())

        game_object.destroy()
        game_object.destroy()

        self.assertTrue(game_object.is_destroyed)
        self.assertEqual(first.destroy_count, 1)
        self.assertEqual(second.destroy_count, 1)
        self.assertEqual(game_object.components, {})
        self.assertEqual(game_object.components_list, [])

    def test_tags_are_unique(self):
        game_object = GameObject()

        game_object.add_tag('enemy')
        game_object.add_tag('enemy')
        game_object.remove_tag('enemy')

        self.assertEqual(game_object.tags, [])
        self.assertFalse(game_object.has_tag('enemy'))


class SceneTests(unittest.TestCase):
    def test_add_and_remove_object_maintains_indices(self):
        scene = Scene('Level')
        game_object = GameObject('Player')
        game_object.add_tag('friendly')

        scene.add_object(game_object)
        scene.add_object(game_object)

        self.assertEqual(scene.get_object_count(), 1)
        self.assertIs(game_object.scene, scene)
        self.assertIs(scene.find_object('Player'), game_object)
        self.assertEqual(scene.find_objects_with_tag('friendly'), [game_object])

        scene.remove_object(game_object)

        self.assertEqual(scene.get_object_count(), 0)
        self.assertIsNone(game_object.scene)
        self.assertIsNone(scene.find_object('Player'))
        self.assertEqual(scene.find_objects_with_tag('friendly'), [])

    def test_tag_changes_update_scene_index(self):
        scene = Scene()
        game_object = GameObject('Enemy')
        scene.add_object(game_object)

        game_object.add_tag('enemy')
        self.assertEqual(scene.find_objects_with_tag('enemy'), [game_object])

        game_object.remove_tag('enemy')
        self.assertEqual(scene.find_objects_with_tag('enemy'), [])

    def test_initialize_starts_existing_components(self):
        scene = Scene()
        game_object = GameObject()
        component = game_object.add_component(RecordingComponent())
        scene.add_object(game_object)

        scene.initialize()

        self.assertEqual(component.start_count, 1)

    def test_update_removes_destroyed_objects(self):
        scene = Scene()
        alive = GameObject('Alive')
        destroyed = GameObject('Destroyed')
        scene.add_object(alive)
        scene.add_object(destroyed)
        destroyed.destroy()

        scene.update(0.1)

        self.assertEqual(scene.game_objects, [alive])
        self.assertIsNone(destroyed.scene)

    def test_inactive_scene_does_not_update_objects(self):
        scene = Scene()
        game_object = GameObject()
        component = game_object.add_component(RecordingComponent())
        scene.add_object(game_object)
        scene.set_active(False)

        scene.update(0.1)

        self.assertEqual(component.updates, [])

    def test_render_uses_z_order(self):
        render_log = []
        scene = Scene()
        back = RecordingGameObject('Back', render_log)
        front = RecordingGameObject('Front', render_log)
        middle = RecordingGameObject('Middle', render_log)
        back.z_order = -1
        front.z_order = 10
        middle.z_order = 2
        scene.add_object(front)
        scene.add_object(back)
        scene.add_object(middle)

        scene.render(object())

        self.assertEqual(render_log, ['Back', 'Middle', 'Front'])

    def test_find_objects_of_type(self):
        scene = Scene()
        base = GameObject('Base')
        specialized = SpecializedGameObject('Specialized')
        scene.add_object(base)
        scene.add_object(specialized)

        self.assertEqual(scene.find_objects_of_type(SpecializedGameObject), [specialized])
        self.assertEqual(scene.find_objects_of_type(GameObject), [base, specialized])

    def test_cleanup_destroys_objects_and_clears_indices(self):
        scene = Scene()
        game_object = GameObject('Enemy')
        game_object.add_tag('enemy')
        component = game_object.add_component(RecordingComponent())
        scene.add_object(game_object)

        scene.cleanup()

        self.assertTrue(game_object.is_destroyed)
        self.assertEqual(component.destroy_count, 1)
        self.assertEqual(scene.game_objects, [])
        self.assertEqual(scene.objects_by_name, {})
        self.assertEqual(scene.objects_by_tag, {})


if __name__ == '__main__':
    unittest.main()
