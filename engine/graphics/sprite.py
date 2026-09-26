"""Sprite component for rendering 2D shapes and cached image assets."""

from typing import Callable, Dict, List, Optional, Sequence

from ..assets.animation import AnimationClip, FrameKey, SpriteAnimation
from ..assets.atlas import SpriteAtlas
from ..math.vector2 import Vector2
from ..scene.game_object import Component
from .renderer import Renderer


class Sprite(Component):
    """Render a geometric shape, image, or animated sprite-atlas frame."""

    def __init__(
        self,
        color: str = '#FFFFFF',
        size: Optional[Vector2] = None,
        shape: str = 'rectangle',
        image=None,
    ):
        super().__init__()
        self.color = color
        self.size = size or Vector2(50, 50)
        self.shape = shape
        self.image = image
        self.outline_color: Optional[str] = None
        self.outline_width = 1
        self.visible = True
        self.alpha = 1.0

        self.animations: Dict[str, SpriteAnimation] = {}
        self.current_animation: Optional[SpriteAnimation] = None
        self.sprite_atlas: Optional[SpriteAtlas] = None
        self.current_sprite_name: Optional[str] = None

        self.shader_effects: Dict[str, object] = {}
        self.tint_color: Optional[str] = None
        self.brightness = 1.0
        self.contrast = 1.0

    def set_color(self, color: str):
        """Set the fallback shape color."""
        self.color = color

    def set_size(self, size: Vector2):
        """Set the shape or logical sprite size."""
        self.size = size

    def set_image(self, image):
        """Set a direct image, or ``None`` to return to shape rendering."""
        self.image = image

    def set_outline(self, color: str, width: int = 1):
        """Set shape outline properties."""
        self.outline_color = color
        self.outline_width = width

    def set_alpha(self, alpha: float):
        """Set sprite transparency metadata from zero to one."""
        self.alpha = max(0.0, min(1.0, alpha))

    def add_animation(
        self,
        name: str,
        frame_indices: Sequence[FrameKey],
        frame_duration: float = 0.1,
        loop: bool = True,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> SpriteAnimation:
        """Create and register independent animation playback state."""
        animation = SpriteAnimation(
            name,
            frame_indices,
            frame_duration,
            loop,
            on_complete,
        )
        self.animations[name] = animation
        return animation

    def add_animation_clip(
        self,
        clip: AnimationClip,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> SpriteAnimation:
        """Register independent playback state for a shared immutable clip."""
        animation = SpriteAnimation.from_clip(clip, on_complete)
        self.animations[clip.name] = animation
        return animation

    def play_animation(self, name: str, reset: bool = True) -> bool:
        """Play a registered animation, returning whether it exists."""
        animation = self.animations.get(name)
        if animation is None:
            return False
        if self.current_animation and self.current_animation is not animation:
            self.current_animation.stop()
        self.current_animation = animation
        animation.play(reset=reset)
        self._select_animation_frame(animation.current_frame_key)
        return True

    def pause_animation(self):
        """Pause the current animation without resetting it."""
        if self.current_animation:
            self.current_animation.pause()

    def resume_animation(self):
        """Resume the current animation."""
        if self.current_animation:
            self.current_animation.resume()

    def stop_animation(self):
        """Stop and deselect the current animation."""
        if self.current_animation:
            self.current_animation.stop()
            self.current_animation = None

    def set_sprite_atlas(
        self,
        atlas: SpriteAtlas,
        sprite_name: Optional[str] = None,
    ):
        """Set an atlas and optionally select its initial region."""
        self.sprite_atlas = atlas
        if sprite_name is not None:
            self.set_current_sprite(sprite_name)

    def set_current_sprite(self, sprite_name: str) -> bool:
        """Select a named atlas region, returning whether it exists."""
        if not self.sprite_atlas or sprite_name not in self.sprite_atlas.sprites:
            return False
        self.current_sprite_name = sprite_name
        return True

    def set_tint(self, color: str):
        """Set tint metadata for shape rendering."""
        self.tint_color = color

    def set_brightness(self, brightness: float):
        """Set brightness metadata from zero to two."""
        self.brightness = max(0.0, min(2.0, brightness))

    def set_contrast(self, contrast: float):
        """Set contrast metadata from zero to two."""
        self.contrast = max(0.0, min(2.0, contrast))

    def add_shader_effect(self, name: str, effect_data: object):
        """Add custom shader metadata."""
        self.shader_effects[name] = effect_data

    def remove_shader_effect(self, name: str):
        """Remove custom shader metadata."""
        self.shader_effects.pop(name, None)

    def get_size(self) -> Vector2:
        """Return the logical sprite size."""
        return self.size.copy()

    def contains_point(self, point: Vector2) -> bool:
        """Check whether a point is inside the sprite's logical bounds."""
        if not self.game_object:
            return False

        world_position = self.game_object.transform.world_position
        world_scale = self.game_object.transform.world_scale
        actual_size = Vector2(
            self.size.x * abs(world_scale.x),
            self.size.y * abs(world_scale.y),
        )

        if self.shape == 'circle':
            radius = max(actual_size.x, actual_size.y) / 2
            return point.distance_squared_to(world_position) <= radius * radius

        half_width = actual_size.x / 2
        half_height = actual_size.y / 2
        return (
            world_position.x - half_width
            <= point.x
            <= world_position.x + half_width
            and world_position.y - half_height
            <= point.y
            <= world_position.y + half_height
        )

    def update(self, delta_time: float):
        """Advance the current animation."""
        if self.current_animation:
            frame_key = self.current_animation.update(delta_time)
            self._select_animation_frame(frame_key)

    def _select_animation_frame(self, frame_key: FrameKey):
        if not self.sprite_atlas:
            return
        if isinstance(frame_key, str):
            frame_name = frame_key
        else:
            frame_name = f"{self.current_animation.name}_frame_{frame_key}"
        self.set_current_sprite(frame_name)

    def render(self, renderer: Renderer):
        """Render the current image, atlas frame, or fallback shape."""
        if not self.visible or not self.game_object:
            return

        transform = self.game_object.transform
        world_position = transform.world_position
        world_rotation = transform.world_rotation
        world_scale = transform.world_scale

        render_color = self.color
        render_size = self.size
        render_image = self.image

        if self.sprite_atlas and self.current_sprite_name:
            sprite_data = self.sprite_atlas.get_sprite_data(self.current_sprite_name)
            if sprite_data:
                render_color = sprite_data['color']
                render_size = sprite_data['size']
                render_image = sprite_data['image']

        if render_image is not None:
            renderer.draw_image(world_position, render_image)
            return

        actual_size = Vector2(
            render_size.x * abs(world_scale.x),
            render_size.y * abs(world_scale.y),
        )
        final_color = self._apply_shader_effects(render_color)

        if self.shape == 'circle':
            radius = max(actual_size.x, actual_size.y) / 2
            renderer.draw_circle(
                world_position,
                radius,
                final_color,
                self.outline_color,
                self.outline_width,
            )
        elif self.shape == 'triangle':
            half_width = actual_size.x / 2
            half_height = actual_size.y / 2
            points = [
                Vector2(0, -half_height),
                Vector2(-half_width, half_height),
                Vector2(half_width, half_height),
            ]
            world_points = [
                world_position + point.rotate(world_rotation)
                for point in points
            ]
            renderer.draw_polygon(
                world_points,
                final_color,
                self.outline_color,
                self.outline_width,
            )
        else:
            renderer.draw_rectangle(
                world_position,
                actual_size,
                final_color,
                world_rotation,
                self.outline_color,
                self.outline_width,
            )

    def _apply_shader_effects(self, base_color: str) -> str:
        color = base_color
        if self.tint_color:
            color = self._blend_colors(color, self.tint_color, 0.5)
        return color

    @staticmethod
    def _blend_colors(color1: str, color2: str, factor: float) -> str:
        return color2 if factor > 0.5 else color1
