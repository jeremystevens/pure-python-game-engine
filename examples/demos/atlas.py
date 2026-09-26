"""Runnable image assets, sprite atlas, and animation demonstration."""

from pathlib import Path

from engine import (
    AnimationClip,
    GameEngine,
    GameObject,
    Sprite,
    SpriteAtlas,
    Vector2,
)


class AnimatedSprite(GameObject):
    """GameObject with independent playback state for a shared animation clip."""

    def __init__(self, name, atlas, clip, position, phase=0.0):
        super().__init__(name)
        self.sprite = self.add_component(Sprite(size=Vector2(64, 64)))
        self.sprite.set_sprite_atlas(atlas, clip.frames[0])
        self.sprite.add_animation_clip(clip)
        self.sprite.play_animation(clip.name)
        if phase:
            self.sprite.update(phase)
        self.transform.position = position


class AtlasDemo(GameEngine):
    """Show image caching, sprite-sheet extraction, and shared animation clips."""

    def __init__(self):
        examples_directory = Path(__file__).resolve().parents[1]
        super().__init__(
            "Asset & Animation Demo",
            (800, 600),
            60,
            asset_root=examples_directory,
        )
        self.animated_sprites = []
        self.is_paused = False
        self.cache_reused = False

    def initialize(self):
        sprite_sheet = self.asset_manager.load_image(
            'assets/pulse_sprite_sheet.png'
        )
        cached_sheet = self.asset_manager.load_image(
            'assets/pulse_sprite_sheet.png'
        )
        self.cache_reused = sprite_sheet is cached_sheet

        preview = GameObject('Sprite Sheet Preview')
        preview.add_component(Sprite(image=sprite_sheet, size=Vector2(320, 64)))
        preview.transform.position = Vector2(400, 115)
        self.current_scene.add_object(preview)

        atlas = SpriteAtlas(Vector2(320, 64), sprite_sheet)
        frame_names = atlas.create_animation_frames(
            'pulse',
            frame_count=5,
            frame_size=Vector2(64, 64),
            start_position=Vector2.zero(),
        )
        clip = AnimationClip.from_frames(
            'pulse',
            frame_names,
            frame_duration=0.14,
            loop=True,
        )

        for index in range(3):
            animated = AnimatedSprite(
                f'Animated Sprite {index + 1}',
                atlas,
                clip,
                Vector2(240 + index * 160, 340),
                phase=index * 0.14,
            )
            self.animated_sprites.append(animated)
            self.current_scene.add_object(animated)

        print("Asset & Animation Demo")
        print(f"Image cache reused object: {self.cache_reused}")
        print("SPACE - pause/resume | R - restart | ESC - quit")

    def update(self, delta_time):
        if self.input_manager.is_key_just_pressed('escape'):
            self.quit()

        if self.input_manager.is_key_just_pressed('space'):
            self.is_paused = not self.is_paused
            for animated in self.animated_sprites:
                if self.is_paused:
                    animated.sprite.pause_animation()
                else:
                    animated.sprite.resume_animation()

        if self.input_manager.is_key_just_pressed('r'):
            self.is_paused = False
            for animated in self.animated_sprites:
                animated.sprite.play_animation('pulse', reset=True)

    def render(self):
        self.renderer.draw_text(
            Vector2(400, 35),
            "ASSET CACHE + SPRITE ATLAS + ANIMATION",
            '#FFFFFF',
            20,
        )
        self.renderer.draw_text(
            Vector2(400, 70),
            "Original 320 x 64 PNG sprite sheet (five atlas regions)",
            '#B8D8FF',
            12,
        )
        state = "PAUSED" if self.is_paused else "PLAYING"
        cache_state = "REUSED" if self.cache_reused else "NOT REUSED"
        self.renderer.draw_text(
            Vector2(400, 235),
            f"Three independent players sharing one clip: {state}",
            '#FFFFFF',
            14,
        )
        self.renderer.draw_text(
            Vector2(400, 440),
            f"Asset cache: {cache_state} | Loaded images: "
            f"{self.asset_manager.image_count}",
            '#80FFB0',
            13,
        )
        self.renderer.draw_text(
            Vector2(400, 500),
            "SPACE pause/resume     R restart     ESC quit",
            '#FFE080',
            14,
        )


if __name__ == "__main__":
    AtlasDemo().run()
