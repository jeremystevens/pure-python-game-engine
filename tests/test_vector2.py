import math
import unittest

from engine.math.vector2 import Vector2
from engine.math.vector3 import Vector3


class Vector2Tests(unittest.TestCase):
    def test_construction_and_copy(self):
        vector = Vector2(2, -3.5)
        copied = vector.copy()

        self.assertEqual(vector.to_tuple(), (2.0, -3.5))
        self.assertEqual(copied, vector)
        self.assertIsNot(copied, vector)

    def test_arithmetic_returns_new_vectors(self):
        vector = Vector2(2, 4)

        self.assertEqual(vector + Vector2(3, -1), Vector2(5, 3))
        self.assertEqual(vector - Vector2(3, -1), Vector2(-1, 5))
        self.assertEqual(vector * 2, Vector2(4, 8))
        self.assertEqual(2 * vector, Vector2(4, 8))
        self.assertEqual(vector / 2, Vector2(1, 2))
        self.assertEqual(vector, Vector2(2, 4))

    def test_division_by_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            Vector2.one() / 0

    def test_magnitude_and_normalization(self):
        vector = Vector2(3, 4)

        self.assertEqual(vector.magnitude, 5)
        self.assertEqual(vector.magnitude_squared, 25)
        self.assertEqual(vector.normalize(), Vector2(0.6, 0.8))
        self.assertEqual(vector.normalized(), Vector2(0.6, 0.8))
        self.assertEqual(Vector2.zero().normalize(), Vector2.zero())

    def test_dot_and_cross_products(self):
        first = Vector2(2, 3)
        second = Vector2(-4, 5)

        self.assertEqual(first.dot(second), 7)
        self.assertEqual(first.cross(second), 22)

    def test_distance(self):
        first = Vector2(1, 2)
        second = Vector2(4, 6)

        self.assertEqual(first.distance_to(second), 5)
        self.assertEqual(first.distance_squared_to(second), 25)

    def test_angle_between_vectors(self):
        self.assertAlmostEqual(Vector2.right().angle_to(Vector2(0, 1)), math.pi / 2)
        self.assertEqual(Vector2.zero().angle_to(Vector2.right()), 0)

    def test_rotation(self):
        rotated = Vector2.right().rotate(math.pi / 2)

        self.assertAlmostEqual(rotated.x, 0)
        self.assertAlmostEqual(rotated.y, 1)

    def test_lerp_interpolates_and_clamps(self):
        start = Vector2(0, 10)
        end = Vector2(10, 20)

        self.assertEqual(start.lerp(end, 0.25), Vector2(2.5, 12.5))
        self.assertEqual(start.lerp(end, -1), start)
        self.assertEqual(start.lerp(end, 2), end)

    def test_direction_factories_use_screen_coordinates(self):
        self.assertEqual(Vector2.zero(), Vector2(0, 0))
        self.assertEqual(Vector2.one(), Vector2(1, 1))
        self.assertEqual(Vector2.up(), Vector2(0, -1))
        self.assertEqual(Vector2.down(), Vector2(0, 1))
        self.assertEqual(Vector2.left(), Vector2(-1, 0))
        self.assertEqual(Vector2.right(), Vector2(1, 0))

    def test_angle_factory_and_conversions(self):
        vector = Vector2.from_angle(math.pi / 2, 3)

        self.assertAlmostEqual(vector.x, 0)
        self.assertAlmostEqual(vector.y, 3)
        self.assertEqual(Vector2(1.9, -2.9).to_int_tuple(), (1, -2))
        self.assertEqual(Vector2(2, 3).to_vector3(4), Vector3(2, 3, 4))


if __name__ == '__main__':
    unittest.main()
