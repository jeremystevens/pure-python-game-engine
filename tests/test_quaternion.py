import math
import unittest

from engine.math.quaternion import Quaternion
from engine.math.vector3 import Vector3


class QuaternionTests(unittest.TestCase):
    def assertVectorAlmostEqual(self, first, second, places=6):
        self.assertAlmostEqual(first.x, second.x, places=places)
        self.assertAlmostEqual(first.y, second.y, places=places)
        self.assertAlmostEqual(first.z, second.z, places=places)

    def assertQuaternionAlmostEqual(self, first, second, places=6):
        self.assertAlmostEqual(first.x, second.x, places=places)
        self.assertAlmostEqual(first.y, second.y, places=places)
        self.assertAlmostEqual(first.z, second.z, places=places)
        self.assertAlmostEqual(first.w, second.w, places=places)

    def test_identity_and_copy(self):
        identity = Quaternion.identity()
        copied = identity.copy()

        self.assertEqual(identity, Quaternion(0, 0, 0, 1))
        self.assertEqual(copied, identity)
        self.assertIsNot(copied, identity)

    def test_arithmetic_and_scalar_multiplication(self):
        first = Quaternion(1, 2, 3, 4)
        second = Quaternion(4, 3, 2, 1)

        self.assertEqual(first + second, Quaternion(5, 5, 5, 5))
        self.assertEqual(first - second, Quaternion(-3, -1, 1, 3))
        self.assertEqual(first * 2, Quaternion(2, 4, 6, 8))
        self.assertEqual(2 * first, Quaternion(2, 4, 6, 8))

    def test_magnitude_and_normalization(self):
        quaternion = Quaternion(1, 2, 2, 0)

        self.assertEqual(quaternion.magnitude, 3)
        self.assertEqual(quaternion.magnitude_squared, 9)
        self.assertQuaternionAlmostEqual(quaternion.normalized(), Quaternion(1 / 3, 2 / 3, 2 / 3, 0))
        self.assertEqual(Quaternion(0, 0, 0, 0).normalize(), Quaternion.identity())

    def test_inverse_cancels_rotation(self):
        quaternion = Quaternion.from_axis_angle(Vector3.up(), math.pi / 3)

        self.assertQuaternionAlmostEqual(quaternion * quaternion.inverse(), Quaternion.identity())
        self.assertEqual(Quaternion(0, 0, 0, 0).inverse(), Quaternion.identity())

    def test_axis_angle_rotates_vector(self):
        rotation = Quaternion.from_axis_angle(Vector3.forward(), math.pi / 2)

        self.assertVectorAlmostEqual(rotation.rotate_vector(Vector3.right()), Vector3.up())

    def test_euler_angle_round_trip(self):
        angles = (0.2, -0.3, 0.4)
        restored = Quaternion.from_euler_angles(*angles).to_euler_angles()

        for actual, expected in zip(restored, angles):
            self.assertAlmostEqual(actual, expected)

    def test_axis_angle_round_trip(self):
        quaternion = Quaternion.from_axis_angle(Vector3.up(), math.pi / 3)
        axis, angle = quaternion.to_axis_angle()

        self.assertVectorAlmostEqual(axis, Vector3.up())
        self.assertAlmostEqual(angle, math.pi / 3)

    def test_lerp_and_slerp_clamp_and_interpolate(self):
        start = Quaternion.identity()
        end = Quaternion.from_axis_angle(Vector3.forward(), math.pi)

        self.assertEqual(start.lerp(end, -1), start)
        self.assertQuaternionAlmostEqual(start.slerp(end, 2), end)

        halfway = start.slerp(end, 0.5)
        self.assertVectorAlmostEqual(halfway.rotate_vector(Vector3.right()), Vector3.up())

    def test_rotation_matrix_identity(self):
        matrix = [
            1, 0, 0,
            0, 1, 0,
            0, 0, 1,
        ]

        self.assertEqual(Quaternion.from_rotation_matrix(matrix), Quaternion.identity())

    def test_look_rotation_preserves_default_forward(self):
        rotation = Quaternion.look_rotation(Vector3.forward())

        self.assertVectorAlmostEqual(rotation.rotate_vector(Vector3.forward()), Vector3.forward())


if __name__ == '__main__':
    unittest.main()
