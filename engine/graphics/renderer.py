"""
The text rendering function `draw_text` is updated to include font style and anchor for improved formatting.
"""
import math
from tkinter import Canvas
from typing import Tuple, Optional, Dict, List
from ..math.vector2 import Vector2


class Renderer:
    """2D renderer using tkinter Canvas"""

    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.width = int(canvas['width'])
        self.height = int(canvas['height'])

        # Shader system
        self.active_shaders: List[str] = []
        self.shader_uniforms: Dict[str, any] = {}
        self.post_processing_effects: List[str] = []

        # Render layers for depth sorting
        self.render_layers: Dict[int, List] = {}
        self.current_layer = 0

    def draw_rectangle(self, position: Vector2, size: Vector2, color: str = '#FFFFFF', 
                      rotation: float = 0.0, outline: str = None, width: int = 1):
        """Draw a rectangle"""
        if rotation == 0:
            # Simple case - no rotation
            x1 = position.x - size.x / 2
            y1 = position.y - size.y / 2
            x2 = position.x + size.x / 2
            y2 = position.y + size.y / 2

            return self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline=outline or color,
                width=width
            )
        else:
            # Rotated rectangle - draw as polygon
            half_w = size.x / 2
            half_h = size.y / 2

            # Rectangle corners (local coordinates)
            corners = [
                Vector2(-half_w, -half_h),
                Vector2(half_w, -half_h),
                Vector2(half_w, half_h),
                Vector2(-half_w, half_h)
            ]

            # Rotate and translate corners
            rotated_corners = []
            for corner in corners:
                rotated = corner.rotate(rotation)
                world_pos = position + rotated
                rotated_corners.extend([world_pos.x, world_pos.y])

            return self.canvas.create_polygon(
                rotated_corners,
                fill=color,
                outline=outline or color,
                width=width
            )

    def draw_circle(self, position: Vector2, radius: float, color: str = '#FFFFFF',
                   outline: str = None, width: int = 1):
        """Draw a circle"""
        x1 = position.x - radius
        y1 = position.y - radius
        x2 = position.x + radius
        y2 = position.y + radius

        return self.canvas.create_oval(
            x1, y1, x2, y2,
            fill=color,
            outline=outline or color,
            width=width
        )

    def draw_line(self, start: Vector2, end: Vector2, color: str = '#FFFFFF', width: int = 1):
        """Draw a line"""
        return self.canvas.create_line(
            start.x, start.y, end.x, end.y,
            fill=color,
            width=width
        )

    def draw_text(self, position: Vector2, text: str, color: str = '#FFFFFF', font_size: int = 12, anchor: str = 'center'):
        """Draw text at position with improved formatting"""
        self.canvas.create_text(
            position.x, position.y,
            text=text,
            fill=color,
            font=('Arial', font_size, 'bold'),
            anchor=anchor
        )

    def draw_image(
        self,
        position: Vector2,
        image,
        anchor: str = 'center',
    ):
        """Draw a Tk-compatible image centered at a world position."""
        if image is None:
            return None
        return self.canvas.create_image(
            position.x,
            position.y,
            image=image,
            anchor=anchor,
        )

    def draw_polygon(self, points: list, color: str = '#FFFFFF',
                    outline: str = None, width: int = 1):
        """Draw a polygon from a list of Vector2 points"""
        coords = []
        for point in points:
            coords.extend([point.x, point.y])

        return self.canvas.create_polygon(
            coords,
            fill=color,
            outline=outline or color,
            width=width
        )

    def clear(self):
        """Clear all drawn objects"""
        self.canvas.delete("all")

    def get_size(self) -> Vector2:
        """Get renderer size"""
        return Vector2(self.width, self.height)

    def get_center(self) -> Vector2:
        """Get center point"""
        return Vector2(self.width / 2, self.height / 2)

    def set_shader(self, shader_name: str, enabled: bool = True):
        """Enable or disable a shader effect"""
        if enabled and shader_name not in self.active_shaders:
            self.active_shaders.append(shader_name)
        elif not enabled and shader_name in self.active_shaders:
            self.active_shaders.remove(shader_name)

    def set_shader_uniform(self, name: str, value: any):
        """Set a shader uniform value"""
        self.shader_uniforms[name] = value

    def add_post_processing_effect(self, effect_name: str):
        """Add a post-processing effect"""
        if effect_name not in self.post_processing_effects:
            self.post_processing_effects.append(effect_name)

    def remove_post_processing_effect(self, effect_name: str):
        """Remove a post-processing effect"""
        if effect_name in self.post_processing_effects:
            self.post_processing_effects.remove(effect_name)

    def set_render_layer(self, layer: int):
        """Set current render layer for depth sorting"""
        self.current_layer = layer
        if layer not in self.render_layers:
            self.render_layers[layer] = []

    def draw_sprite_from_atlas(self, position: Vector2, atlas_data: Dict, 
                              rotation: float = 0.0, scale: Vector2 = None):
        """Draw a sprite from an atlas with UV coordinates"""
        if not atlas_data:
            return

        sprite_size = atlas_data['size']
        sprite_color = atlas_data['color']

        if scale:
            sprite_size = Vector2(sprite_size.x * scale.x, sprite_size.y * scale.y)

        # For now, just draw as a rectangle since we're using tkinter
        # In a real implementation, this would use UV coordinates for texture sampling
        return self.draw_rectangle(position, sprite_size, sprite_color, rotation)

    def apply_post_processing(self):
        """Apply post-processing effects to the rendered frame"""
        # Simplified post-processing simulation
        for effect in self.post_processing_effects:
            if effect == "bloom":
                self._apply_bloom_effect()
            elif effect == "blur":
                self._apply_blur_effect()
            elif effect == "vintage":
                self._apply_vintage_effect()

    def _apply_bloom_effect(self):
        """Apply bloom post-processing effect (simplified)"""
        # In a real implementation, this would apply bloom to bright areas
        pass

    def _apply_blur_effect(self):
        """Apply blur post-processing effect (simplified)"""
        # In a real implementation, this would blur the entire frame
        pass

    def _apply_vintage_effect(self):
        """Apply vintage post-processing effect (simplified)"""
        # In a real implementation, this would adjust colors for vintage look
        pass

    def render_layers(self):
        """Render all layers in order"""
        for layer in sorted(self.render_layers.keys()):
            for render_command in self.render_layers[layer]:
                render_command()

        # Clear layers after rendering
        self.render_layers.clear()

    def flush_render_queue(self):
        """Process the render queue and apply post-processing"""
        self.render_layers()
        self.apply_post_processing()