import unittest

from engine.assets import SpriteAtlas
from engine.math.vector2 import Vector2


class RecordingFrameFactory:
    def __init__(self):
        self.calls = []

    def __call__(self, source, region):
        frame = object()
        self.calls.append((source, region, frame))
        return frame


class SpriteAtlasTests(unittest.TestCase):
    def test_texture_and_region_dimensions_are_validated(self):
        with self.assertRaises(ValueError):
            SpriteAtlas(Vector2(0, 64))

        atlas = SpriteAtlas(Vector2(64, 64))
        with self.assertRaises(ValueError):
            atlas.add_sprite('', Vector2.zero(), Vector2(8, 8))
        with self.assertRaises(ValueError):
            atlas.add_sprite('negative', Vector2(-1, 0), Vector2(8, 8))
        with self.assertRaises(ValueError):
            atlas.add_sprite('empty', Vector2.zero(), Vector2(0, 8))
        with self.assertRaisesRegex(ValueError, 'atlas width'):
            atlas.add_sprite('wide', Vector2(60, 0), Vector2(8, 8))
        with self.assertRaisesRegex(ValueError, 'atlas height'):
            atlas.add_sprite('tall', Vector2(0, 60), Vector2(8, 8))
        with self.assertRaisesRegex(ValueError, 'whole pixels'):
            atlas.add_sprite('fractional', Vector2(0.5, 0), Vector2(8, 8))

    def test_region_metadata_and_uv_coordinates(self):
        atlas = SpriteAtlas(Vector2(100, 50))
        atlas.add_sprite(
            'player',
            Vector2(20, 10),
            Vector2(30, 20),
            color='#123456',
        )

        data = atlas.get_sprite_data('player')

        self.assertEqual(data['position'], Vector2(20, 10))
        self.assertEqual(data['size'], Vector2(30, 20))
        self.assertEqual(data['color'], '#123456')
        self.assertEqual(data['uv_start'], Vector2(0.2, 0.2))
        self.assertEqual(data['uv_end'], Vector2(0.5, 0.6))
        self.assertIsNone(data['image'])
        self.assertIsNone(atlas.get_sprite_data('missing'))

    def test_frames_are_extracted_lazily_and_cached(self):
        source = object()
        factory = RecordingFrameFactory()
        atlas = SpriteAtlas(Vector2(64, 32), source, factory)
        atlas.add_sprite('first', Vector2.zero(), Vector2(32, 32))

        self.assertEqual(atlas.frame_count, 0)
        first = atlas.get_frame('first')
        second = atlas.get_frame('first')

        self.assertIs(first, second)
        self.assertEqual(len(factory.calls), 1)
        self.assertIs(factory.calls[0][0], source)
        self.assertEqual(factory.calls[0][1].name, 'first')
        self.assertEqual(atlas.frame_count, 1)

    def test_replacing_region_invalidates_its_cached_frame(self):
        factory = RecordingFrameFactory()
        atlas = SpriteAtlas(Vector2(64, 32), object(), factory)
        atlas.add_sprite('frame', Vector2.zero(), Vector2(32, 32))
        first = atlas.get_frame('frame')

        atlas.add_sprite('frame', Vector2(32, 0), Vector2(32, 32))
        second = atlas.get_frame('frame')

        self.assertIsNot(first, second)
        self.assertEqual(len(factory.calls), 2)
        self.assertEqual(factory.calls[1][1].position, Vector2(32, 0))

    def test_clear_frames_keeps_region_definitions(self):
        atlas = SpriteAtlas(Vector2(32, 32), object(), RecordingFrameFactory())
        atlas.add_sprite('frame', Vector2.zero(), Vector2(32, 32))
        atlas.get_frame('frame')

        atlas.clear_frames()

        self.assertEqual(atlas.frame_count, 0)
        self.assertIn('frame', atlas.sprites)

    def test_unknown_frame_raises_key_error(self):
        atlas = SpriteAtlas(Vector2(32, 32), object(), RecordingFrameFactory())
        with self.assertRaisesRegex(KeyError, 'missing'):
            atlas.get_frame('missing')

    def test_horizontal_and_vertical_animation_regions(self):
        horizontal = SpriteAtlas(Vector2(48, 16))
        horizontal_names = horizontal.create_animation_frames(
            'walk', 3, Vector2(16, 16), Vector2.zero(), horizontal=True
        )
        self.assertEqual(
            horizontal_names,
            ['walk_frame_0', 'walk_frame_1', 'walk_frame_2'],
        )
        self.assertEqual(
            horizontal.sprites['walk_frame_2']['position'],
            Vector2(32, 0),
        )

        vertical = SpriteAtlas(Vector2(16, 48))
        vertical.create_animation_frames(
            'climb', 3, Vector2(16, 16), Vector2.zero(), horizontal=False
        )
        self.assertEqual(
            vertical.sprites['climb_frame_2']['position'],
            Vector2(0, 32),
        )

    def test_animation_frame_count_must_be_positive(self):
        atlas = SpriteAtlas(Vector2(32, 32))
        with self.assertRaises(ValueError):
            atlas.create_animation_frames(
                'empty', 0, Vector2(16, 16), Vector2.zero()
            )


if __name__ == '__main__':
    unittest.main()
