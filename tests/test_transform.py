import math
import unittest

from engine.math.quaternion import Quaternion
from engine.math.transform import Transform
from engine.math.vector2 import Vector2


class TransformTests(unittest.TestCase):
    def test_default_values_are_independent(self):
        first = Transform()
        second = Transform()

        first.position.x = 5
        first.scale.y = 3

        self.assertEqual(second.position, Vector2.zero())
        self.assertEqual(second.scale, Vector2.one())

    def test_root_world_values_are_copies(self):
        transform = Transform(Vector2(2, 3), 0.5, Vector2(4, 5))

        world_position = transform.world_position
        world_scale = transform.world_scale
        world_position.x = 100
        world_scale.x = 100

        self.assertEqual(transform.position, Vector2(2, 3))
        self.assertEqual(transform.scale, Vector2(4, 5))
        self.assertEqual(transform.world_rotation, 0.5)

    def test_parenting_tracks_children_and_reparenting(self):
        first_parent = Transform()
        second_parent = Transform()
        child = Transform()

        child.parent = first_parent
        self.assertIs(child.parent, first_parent)
        self.assertIn(child, first_parent.children)

        child.parent = second_parent
        self.assertNotIn(child, first_parent.children)
        self.assertIn(child, second_parent.children)

        child.parent = None
        self.assertIsNone(child.parent)
        self.assertNotIn(child, second_parent.children)

    def test_children_returns_a_copy(self):
        parent = Transform()
        child = Transform()
        child.parent = parent

        children = parent.children
        children.clear()

        self.assertEqual(parent.children, [child])

    def test_world_transform_combines_parent_values(self):
        parent = Transform(Vector2(10, 20), math.pi / 2, Vector2(2, 3))
        child = Transform(Vector2(1, 2), math.pi / 4, Vector2(4, 5))
        child.parent = parent

        self.assertEqual(child.world_position, Vector2(4, 22))
        self.assertAlmostEqual(child.world_rotation, 3 * math.pi / 4)
        self.assertEqual(child.world_scale, Vector2(8, 15))

    def test_translate_rotate_and_scale(self):
        transform = Transform()

        transform.translate(Vector2(2, 3))
        transform.rotate(math.pi / 4)
        transform.scale_by(Vector2(2, 4))

        self.assertEqual(transform.position, Vector2(2, 3))
        self.assertAlmostEqual(transform.rotation, math.pi / 4)
        self.assertEqual(transform.scale, Vector2(2, 4))

    def test_look_at_and_direction_vectors(self):
        transform = Transform(Vector2(2, 2))
        transform.look_at(Vector2(2, 5))

        self.assertAlmostEqual(transform.rotation, math.pi / 2)
        self.assertEqual(transform.forward(), Vector2(0, 1))
        self.assertEqual(transform.right(), Vector2(-1, 0))

    def test_transform_point_round_trip(self):
        transform = Transform(Vector2(10, -5), math.pi / 3, Vector2(2, 4))
        local_point = Vector2(3, -2)

        world_point = transform.transform_point(local_point)

        self.assertEqual(transform.inverse_transform_point(world_point), local_point)

    def test_3d_mode_lifecycle(self):
        transform = Transform()

        self.assertIsNone(transform.quaternion_rotation)
        transform.enable_3d()
        self.assertEqual(transform.quaternion_rotation, Quaternion.identity())

        rotation = Quaternion.from_euler_angles(0, 0, math.pi / 2)
        transform.quaternion_rotation = rotation
        self.assertIs(transform.quaternion_rotation, rotation)

        transform.disable_3d()
        self.assertIsNone(transform.quaternion_rotation)

    def test_quaternion_conversion_preserves_z_rotation(self):
        transform = Transform(rotation=math.pi / 3)
        quaternion = transform.get_quaternion_from_rotation()

        restored = Transform()
        restored.set_rotation_from_quaternion(quaternion)

        self.assertAlmostEqual(restored.rotation, transform.rotation)


if __name__ == '__main__':
    unittest.main()
