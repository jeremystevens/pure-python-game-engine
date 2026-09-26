import unittest

from engine.graphics.sprite import Sprite
from engine.math.vector2 import Vector2
from engine.scene.game_object import GameObject


class SpriteGeometryTests(unittest.TestCase):
    def test_unattached_sprite_contains_no_points(self):
        sprite = Sprite(size=Vector2(10, 10))

        self.assertFalse(sprite.contains_point(Vector2.zero()))

    def test_rectangle_contains_interior_and_boundary_points(self):
        game_object = GameObject()
        game_object.transform.position = Vector2(10, 20)
        sprite = game_object.add_component(Sprite(size=Vector2(8, 4)))

        self.assertTrue(sprite.contains_point(Vector2(10, 20)))
        self.assertTrue(sprite.contains_point(Vector2(14, 22)))
        self.assertFalse(sprite.contains_point(Vector2(14.01, 22)))
        self.assertFalse(sprite.contains_point(Vector2(10, 22.01)))

    def test_rectangle_uses_world_scale(self):
        game_object = GameObject()
        game_object.transform.scale = Vector2(2, 3)
        sprite = game_object.add_component(Sprite(size=Vector2(10, 10)))

        self.assertTrue(sprite.contains_point(Vector2(10, 15)))
        self.assertFalse(sprite.contains_point(Vector2(10.01, 15)))

    def test_circle_uses_largest_scaled_dimension_as_diameter(self):
        game_object = GameObject()
        game_object.transform.position = Vector2(5, 5)
        game_object.transform.scale = Vector2(2, 1)
        sprite = game_object.add_component(Sprite(size=Vector2(10, 10), shape='circle'))

        self.assertTrue(sprite.contains_point(Vector2(15, 5)))
        self.assertFalse(sprite.contains_point(Vector2(15.01, 5)))


if __name__ == '__main__':
    unittest.main()
