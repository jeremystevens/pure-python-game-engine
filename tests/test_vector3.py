import math
import unittest

from engine.math.vector2 import Vector2
from engine.math.vector3 import Vector3


class Vector3Tests(unittest.TestCase):
    def test_construction_and_copy(self):
        vector = Vector3(2, -3.5, 7)
        copied = vector.copy()

        self.assertEqual(vector.to_tuple(), (2.0, -3.5, 7.0))
        self.assertEqual(copied, vector)
        self.assertIsNot(copied, vector)

    def test_arithmetic_returns_new_vectors(self):
        vector = Vector3(2, 4, 6)

        self.assertEqual(vector + Vector3(3, -1, 2), Vector3(5, 3, 8))
        self.assertEqual(vector - Vector3(3, -1, 2), Vector3(-1, 5, 4))
        self.assertEqual(vector * 2, Vector3(4, 8, 12))
        self.assertEqual(2 * vector, Vector3(4, 8, 12))
        self.assertEqual(vector / 2, Vector3(1, 2, 3))
        self.assertEqual(vector, Vector3(2, 4, 6))

    def test_division_by_zero_raises_value_error(self):
        with self.assertRaises(ValueError):
            Vector3.one() / 0

    def test_magnitude_and_normalization(self):
        vector = Vector3(2, 3, 6)

        self.assertEqual(vector.magnitude, 7)
        self.assertEqual(vector.magnitude_squared, 49)
        self.assertEqual(vector.normalize(), Vector3(2 / 7, 3 / 7, 6 / 7))
        self.assertEqual(Vector3.zero().normalize(), Vector3.zero())

    def test_dot_and_cross_products(self):
        self.assertEqual(Vector3(1, 2, 3).dot(Vector3(4, 5, 6)), 32)
        self.assertEqual(Vector3.right().cross(Vector3.up()), Vector3.forward())
        self.assertEqual(Vector3.up().cross(Vector3.right()), Vector3.back())

    def test_distance_and_angle(self):
        first = Vector3(1, 2, 3)
        second = Vector3(3, 5, 9)

        self.assertEqual(first.distance_squared_to(second), 49)
        self.assertEqual(first.distance_to(second), 7)
        self.assertAlmostEqual(Vector3.right().angle_to(Vector3.up()), math.pi / 2)
        self.assertEqual(Vector3.zero().angle_to(Vector3.right()), 0)

    def test_lerp_interpolates_and_clamps(self):
        start = Vector3(0, 10, 20)
        end = Vector3(10, 20, 30)

        self.assertEqual(start.lerp(end, 0.25), Vector3(2.5, 12.5, 22.5))
        self.assertEqual(start.lerp(end, -1), start)
        self.assertEqual(start.lerp(end, 2), end)

    def test_projection_onto_plane(self):
        projected = Vector3(2, 3, 4).project_onto_plane(Vector3.up())

        self.assertEqual(projected, Vector3(2, 0, 4))

    def test_reflection(self):
        reflected = Vector3(1, -2, 0).reflect(Vector3.up())

        self.assertEqual(reflected, Vector3(1, 2, 0))

    def test_direction_factories(self):
        self.assertEqual(Vector3.zero(), Vector3(0, 0, 0))
        self.assertEqual(Vector3.one(), Vector3(1, 1, 1))
        self.assertEqual(Vector3.up(), Vector3(0, 1, 0))
        self.assertEqual(Vector3.down(), Vector3(0, -1, 0))
        self.assertEqual(Vector3.left(), Vector3(-1, 0, 0))
        self.assertEqual(Vector3.right(), Vector3(1, 0, 0))
        self.assertEqual(Vector3.forward(), Vector3(0, 0, 1))
        self.assertEqual(Vector3.back(), Vector3(0, 0, -1))

    def test_vector2_conversions(self):
        self.assertEqual(Vector3(2, 3, 4).to_vector2(), Vector2(2, 3))
        self.assertEqual(Vector3.from_vector2(Vector2(2, 3), 4), Vector3(2, 3, 4))


if __name__ == '__main__':
    unittest.main()
