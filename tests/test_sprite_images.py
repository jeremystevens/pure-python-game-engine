import unittest

from engine.assets import AnimationClip, SpriteAtlas
from engine.graphics.renderer import Renderer
from engine.graphics.sprite import Sprite
from engine.math.vector2 import Vector2
from engine.scene.game_object import GameObject


class FakeCanvas:
    def __init__(self):
        self.calls = []

    def __getitem__(self, key):
        return {'width': '800', 'height': '600'}[key]

    def create_image(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return 42


class RecordingRenderer:
    def __init__(self):
        self.images = []
        self.rectangles = []

    def draw_image(self, position, image, anchor='center'):
        self.images.append((position, image, anchor))

    def draw_rectangle(self, position, size, color, rotation, outline, width):
        self.rectangles.append((position, size, color, rotation, outline, width))

    def draw_circle(self, *args, **kwargs):
        pass

    def draw_polygon(self, *args, **kwargs):
        pass


class RendererImageTests(unittest.TestCase):
    def test_draw_image_delegates_to_canvas(self):
        canvas = FakeCanvas()
        renderer = Renderer(canvas)
        image = object()

        item = renderer.draw_image(Vector2(12, 34), image, anchor='nw')

        self.assertEqual(item, 42)
        self.assertEqual(
            canvas.calls,
            [((12.0, 34.0), {'image': image, 'anchor': 'nw'})],
        )

    def test_draw_image_ignores_none(self):
        canvas = FakeCanvas()
        renderer = Renderer(canvas)

        self.assertIsNone(renderer.draw_image(Vector2.zero(), None))
        self.assertEqual(canvas.calls, [])


class SpriteImageTests(unittest.TestCase):
    def make_sprite(self, image=None):
        game_object = GameObject()
        game_object.transform.position = Vector2(20, 30)
        sprite = game_object.add_component(Sprite(image=image))
        return game_object, sprite

    def test_direct_image_takes_precedence_over_fallback_shape(self):
        image = object()
        _, sprite = self.make_sprite(image)
        renderer = RecordingRenderer()

        sprite.render(renderer)

        self.assertEqual(renderer.images, [(Vector2(20, 30), image, 'center')])
        self.assertEqual(renderer.rectangles, [])

    def test_clearing_direct_image_restores_shape_rendering(self):
        _, sprite = self.make_sprite(object())
        renderer = RecordingRenderer()

        sprite.set_image(None)
        sprite.render(renderer)

        self.assertEqual(renderer.images, [])
        self.assertEqual(len(renderer.rectangles), 1)

    def test_atlas_frame_takes_precedence_over_direct_image(self):
        direct_image = object()
        atlas_image = object()
        extracted_frame = object()
        atlas = SpriteAtlas(
            Vector2(16, 16),
            atlas_image,
            lambda source, region: extracted_frame,
        )
        atlas.add_sprite('idle', Vector2.zero(), Vector2(16, 16))
        _, sprite = self.make_sprite(direct_image)
        sprite.set_sprite_atlas(atlas, 'idle')
        renderer = RecordingRenderer()

        sprite.render(renderer)

        self.assertEqual(
            renderer.images,
            [(Vector2(20, 30), extracted_frame, 'center')],
        )

    def test_named_animation_frames_select_atlas_regions(self):
        frames = {'walk_0': object(), 'walk_1': object()}
        atlas = SpriteAtlas(
            Vector2(32, 16),
            object(),
            lambda source, region: frames[region.name],
        )
        atlas.add_sprite('walk_0', Vector2.zero(), Vector2(16, 16))
        atlas.add_sprite('walk_1', Vector2(16, 0), Vector2(16, 16))
        _, sprite = self.make_sprite()
        sprite.set_sprite_atlas(atlas)
        clip = AnimationClip.from_frames('walk', ['walk_0', 'walk_1'], 0.1)
        sprite.add_animation_clip(clip)

        self.assertTrue(sprite.play_animation('walk'))
        self.assertEqual(sprite.current_sprite_name, 'walk_0')
        sprite.update(0.1)
        self.assertEqual(sprite.current_sprite_name, 'walk_1')

        renderer = RecordingRenderer()
        sprite.render(renderer)
        self.assertEqual(renderer.images[0][1], frames['walk_1'])

    def test_numeric_frames_keep_legacy_atlas_naming(self):
        atlas = SpriteAtlas(Vector2(32, 16))
        atlas.create_animation_frames(
            'walk', 2, Vector2(16, 16), Vector2.zero()
        )
        _, sprite = self.make_sprite()
        sprite.set_sprite_atlas(atlas)
        sprite.add_animation('walk', [0, 1], 0.1)

        sprite.play_animation('walk')
        sprite.update(0.1)

        self.assertEqual(sprite.current_sprite_name, 'walk_frame_1')

    def test_animation_controls_and_missing_names(self):
        _, sprite = self.make_sprite()
        animation = sprite.add_animation('idle', [0, 1], 0.1)

        self.assertFalse(sprite.play_animation('missing'))
        self.assertTrue(sprite.play_animation('idle'))
        sprite.pause_animation()
        self.assertFalse(animation.is_playing)
        sprite.resume_animation()
        self.assertTrue(animation.is_playing)
        sprite.stop_animation()
        self.assertIsNone(sprite.current_animation)
        self.assertEqual(animation.current_frame, 0)

    def test_invalid_atlas_sprite_name_is_rejected(self):
        atlas = SpriteAtlas(Vector2(16, 16))
        _, sprite = self.make_sprite()
        sprite.set_sprite_atlas(atlas)

        self.assertFalse(sprite.set_current_sprite('missing'))
        self.assertIsNone(sprite.current_sprite_name)


if __name__ == '__main__':
    unittest.main()
