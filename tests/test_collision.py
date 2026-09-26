import math
import unittest

from engine.collision import (
    AABB,
    AABBCollider,
    Circle,
    CircleCollider,
    PointCollider,
    aabbs_intersect,
    circle_intersects_aabb,
    circles_intersect,
    point_in_aabb,
    point_in_circle,
    shapes_intersect,
)
from engine.math.vector2 import Vector2
from engine.scene.game_object import GameObject
from engine.scene.scene import Scene


class CollisionGeometryTests(unittest.TestCase):
    def test_shapes_reject_negative_dimensions(self):
        with self.assertRaises(ValueError):
            Circle(Vector2.zero(), -1)
        with self.assertRaises(ValueError):
            AABB(Vector2.zero(), Vector2(-1, 1))

    def test_point_in_circle_includes_boundary(self):
        circle = Circle(Vector2(2, 3), 5)

        self.assertTrue(point_in_circle(Vector2(2, 3), circle))
        self.assertTrue(point_in_circle(Vector2(7, 3), circle))
        self.assertFalse(point_in_circle(Vector2(7.01, 3), circle))

    def test_point_in_aabb_includes_boundary(self):
        box = AABB.from_size(Vector2(10, 20), Vector2(8, 4))

        self.assertEqual(box.minimum, Vector2(6, 18))
        self.assertEqual(box.maximum, Vector2(14, 22))
        self.assertTrue(point_in_aabb(Vector2(14, 22), box))
        self.assertFalse(point_in_aabb(Vector2(14.01, 22), box))

    def test_circle_circle_intersection_includes_touching(self):
        first = Circle(Vector2.zero(), 2)

        self.assertTrue(circles_intersect(first, Circle(Vector2(4, 0), 2)))
        self.assertFalse(circles_intersect(first, Circle(Vector2(4.01, 0), 2)))

    def test_aabb_intersection_includes_touching(self):
        first = AABB.from_size(Vector2.zero(), Vector2(4, 4))

        self.assertTrue(
            aabbs_intersect(first, AABB.from_size(Vector2(4, 0), Vector2(4, 2)))
        )
        self.assertFalse(
            aabbs_intersect(first, AABB.from_size(Vector2(4.01, 0), Vector2(4, 2)))
        )

    def test_circle_aabb_intersection_handles_edges_and_corners(self):
        box = AABB.from_size(Vector2.zero(), Vector2(4, 4))

        self.assertTrue(circle_intersects_aabb(Circle(Vector2(3, 0), 1), box))
        self.assertTrue(
            circle_intersects_aabb(Circle(Vector2(3, 3), math.sqrt(2)), box)
        )
        self.assertFalse(circle_intersects_aabb(Circle(Vector2(3, 3), 1.4), box))

    def test_shape_dispatch_is_symmetric(self):
        circle = Circle(Vector2(3, 0), 1)
        box = AABB.from_size(Vector2.zero(), Vector2(4, 4))

        self.assertTrue(shapes_intersect(circle, box))
        self.assertTrue(shapes_intersect(box, circle))
        self.assertTrue(shapes_intersect(circle, Circle(Vector2(4, 0), 0)))
        self.assertTrue(shapes_intersect(box, AABB(Vector2(4, 0), Vector2(2, 1))))

    def test_shape_dispatch_rejects_unknown_shapes(self):
        with self.assertRaises(TypeError):
            shapes_intersect(object(), object())


class ColliderComponentTests(unittest.TestCase):
    def test_colliders_reject_negative_configuration(self):
        with self.assertRaises(ValueError):
            CircleCollider(-1)
        with self.assertRaises(ValueError):
            AABBCollider(Vector2(-1, 2))
        with self.assertRaises(ValueError):
            CircleCollider(1, layer=-1)
        with self.assertRaises(ValueError):
            CircleCollider(1, mask=-1)

    def test_point_collider_uses_world_transform_and_offset(self):
        game_object = GameObject()
        game_object.transform.position = Vector2(10, 20)
        collider = game_object.add_component(PointCollider(offset=Vector2(2, 3)))

        self.assertEqual(collider.shape, Circle(Vector2(12, 23), 0))
        self.assertTrue(collider.contains_point(Vector2(12, 23)))
        self.assertFalse(collider.contains_point(Vector2(12.01, 23)))

    def test_circle_uses_world_transform_for_center_and_radius(self):
        game_object = GameObject()
        game_object.transform.position = Vector2(10, 20)
        game_object.transform.rotation = math.pi / 2
        game_object.transform.scale = Vector2(2, 3)
        collider = game_object.add_component(
            CircleCollider(2, offset=Vector2(1, 0))
        )

        self.assertEqual(collider.world_center, Vector2(10, 22))
        self.assertEqual(collider.shape.center, Vector2(10, 22))
        self.assertEqual(collider.shape.radius, 6)

    def test_aabb_uses_absolute_world_scale(self):
        game_object = GameObject()
        game_object.transform.position = Vector2(5, 6)
        game_object.transform.scale = Vector2(-2, 3)
        collider = game_object.add_component(AABBCollider(Vector2(10, 4)))

        self.assertEqual(collider.shape.center, Vector2(5, 6))
        self.assertEqual(collider.shape.half_size, Vector2(10, 6))
        self.assertTrue(collider.contains_point(Vector2(15, 12)))
        self.assertFalse(collider.contains_point(Vector2(15.01, 12)))

    def test_layer_filtering_must_be_mutual(self):
        first = CircleCollider(1, layer=0b0001, mask=0b0010)
        second = CircleCollider(1, layer=0b0010, mask=0b0001)

        self.assertTrue(first.can_collide_with(second))
        second.mask = 0b0100
        self.assertFalse(first.can_collide_with(second))

    def test_callbacks_can_be_registered_removed_and_dispatched(self):
        first = CircleCollider(1)
        second = CircleCollider(1)
        events = []
        enter = first.on_enter(lambda other: events.append(('enter', other)))
        stay = first.on_stay(lambda other: events.append(('stay', other)))
        exit_callback = first.on_exit(lambda other: events.append(('exit', other)))

        first._emit_enter(second)
        first._emit_stay(second)
        first._emit_exit(second)

        self.assertEqual(
            events,
            [('enter', second), ('stay', second), ('exit', second)],
        )
        self.assertTrue(first.remove_enter_callback(enter))
        self.assertTrue(first.remove_stay_callback(stay))
        self.assertTrue(first.remove_exit_callback(exit_callback))
        self.assertFalse(first.remove_enter_callback(enter))


class CollisionSystemTests(unittest.TestCase):
    def make_circle(
        self,
        scene,
        name,
        position,
        radius=1,
        layer=1,
        mask=CircleCollider.ALL_LAYERS,
    ):
        game_object = GameObject(name)
        game_object.transform.position = position
        collider = game_object.add_component(CircleCollider(radius, layer=layer, mask=mask))
        scene.add_object(game_object)
        return game_object, collider

    def test_scene_dispatches_enter_stay_and_exit_to_both_colliders(self):
        scene = Scene()
        first_object, first = self.make_circle(scene, 'First', Vector2.zero())
        _, second = self.make_circle(scene, 'Second', Vector2(1, 0))
        events = []
        first.on_enter(lambda other: events.append(('first-enter', other)))
        second.on_enter(lambda other: events.append(('second-enter', other)))
        first.on_stay(lambda other: events.append(('first-stay', other)))
        second.on_stay(lambda other: events.append(('second-stay', other)))
        first.on_exit(lambda other: events.append(('first-exit', other)))
        second.on_exit(lambda other: events.append(('second-exit', other)))

        scene.update(0.1)
        self.assertEqual(
            events,
            [('first-enter', second), ('second-enter', first)],
        )
        self.assertEqual(scene.collision_system.active_pair_count, 1)

        scene.update(0.1)
        self.assertEqual(
            events[-2:],
            [('first-stay', second), ('second-stay', first)],
        )

        first_object.transform.position = Vector2(10, 0)
        scene.update(0.1)
        self.assertEqual(
            events[-2:],
            [('first-exit', second), ('second-exit', first)],
        )
        self.assertEqual(scene.collision_system.active_pair_count, 0)

    def test_layers_and_masks_filter_contacts(self):
        scene = Scene()
        _, first = self.make_circle(
            scene,
            'First',
            Vector2.zero(),
            layer=0b0001,
            mask=0b0010,
        )
        self.make_circle(
            scene,
            'Second',
            Vector2.zero(),
            layer=0b0010,
            mask=0b0100,
        )
        events = []
        first.on_enter(events.append)

        scene.update(0.1)

        self.assertEqual(events, [])
        self.assertEqual(scene.collision_system.active_pair_count, 0)

    def test_inactive_and_destroyed_objects_are_not_detected(self):
        scene = Scene()
        first_object, first = self.make_circle(scene, 'First', Vector2.zero())
        second_object, second = self.make_circle(scene, 'Second', Vector2.zero())
        exits = []
        first.on_exit(lambda other: exits.append(other))
        scene.update(0.1)

        second.is_active = False
        scene.update(0.1)
        self.assertEqual(exits, [second])
        self.assertEqual(scene.collision_system.active_pair_count, 0)

        second.is_active = True
        second_object.destroy()
        first_object.set_active(False)
        scene.update(0.1)
        self.assertEqual(scene.collision_system.active_pair_count, 0)

    def test_destroying_an_object_in_callback_is_safe(self):
        scene = Scene()
        _, first = self.make_circle(scene, 'First', Vector2.zero())
        second_object, second = self.make_circle(scene, 'Second', Vector2.zero())
        events = []

        def destroy_other(other):
            events.append('first-enter')
            other.game_object.destroy()

        first.on_enter(destroy_other)
        second.on_enter(lambda other: events.append('second-enter'))
        first.on_exit(lambda other: events.append('first-exit'))

        scene.update(0.1)
        self.assertEqual(events, ['first-enter'])
        self.assertNotIn(second_object, scene.game_objects)

        scene.update(0.1)
        self.assertEqual(events, ['first-enter', 'first-exit'])
        self.assertEqual(scene.collision_system.active_pair_count, 0)

    def test_objects_added_in_callback_wait_until_the_next_update(self):
        scene = Scene()
        _, first = self.make_circle(scene, 'First', Vector2.zero())
        self.make_circle(scene, 'Second', Vector2.zero())
        events = []
        added = False

        def add_third(other):
            nonlocal added
            events.append('enter')
            if not added:
                added = True
                self.make_circle(scene, 'Third', Vector2.zero())

        first.on_enter(add_third)

        scene.update(0.1)
        self.assertEqual(events, ['enter'])
        self.assertEqual(scene.collision_system.active_pair_count, 1)

        scene.update(0.1)
        self.assertEqual(events, ['enter', 'enter'])
        self.assertEqual(scene.collision_system.active_pair_count, 3)

    def test_colliders_on_the_same_game_object_do_not_contact_each_other(self):
        scene = Scene()
        game_object = GameObject()
        circle = game_object.add_component(CircleCollider(10))
        game_object.add_component(AABBCollider(Vector2(10, 10)))
        scene.add_object(game_object)
        events = []
        circle.on_enter(events.append)

        scene.update(0.1)

        self.assertEqual(events, [])
        self.assertEqual(scene.collision_system.active_pair_count, 0)

    def test_scene_cleanup_clears_active_contacts(self):
        scene = Scene()
        self.make_circle(scene, 'First', Vector2.zero())
        self.make_circle(scene, 'Second', Vector2.zero())
        scene.update(0.1)
        self.assertEqual(scene.collision_system.active_pair_count, 1)

        scene.cleanup()

        self.assertEqual(scene.collision_system.active_pair_count, 0)
        self.assertEqual(scene.game_objects, [])


if __name__ == '__main__':
    unittest.main()
