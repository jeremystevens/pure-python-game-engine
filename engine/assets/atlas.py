"""Sprite-sheet region definitions and lazily extracted image frames."""

from dataclasses import dataclass
import tkinter as tk
from typing import Callable, Dict, List, Optional

from ..math.vector2 import Vector2


@dataclass(frozen=True)
class AtlasRegion:
    """A named rectangular region inside a sprite sheet."""

    name: str
    position: Vector2
    size: Vector2
    color: str = '#FFFFFF'


FrameFactory = Callable[[object, AtlasRegion], object]


class SpriteAtlas:
    """Describe sprite-sheet regions and cache extracted image frames."""

    def __init__(
        self,
        texture_size: Vector2,
        image=None,
        frame_factory: Optional[FrameFactory] = None,
    ):
        if texture_size.x <= 0 or texture_size.y <= 0:
            raise ValueError("texture_size components must be greater than zero")
        self.texture_size = texture_size.copy()
        self.image = image
        self._frame_factory = frame_factory or self._extract_photo_image
        self.sprites: Dict[str, Dict] = {}
        self._frames: Dict[str, object] = {}

    @property
    def frame_count(self) -> int:
        """Return the number of extracted image frames in the cache."""
        return len(self._frames)

    def add_sprite(
        self,
        name: str,
        position: Vector2,
        size: Vector2,
        color: str = '#FFFFFF',
    ):
        """Add or replace a named sprite-sheet region."""
        self._validate_region(name, position, size)
        region = AtlasRegion(name, position.copy(), size.copy(), color)
        self.sprites[name] = {
            'position': region.position,
            'size': region.size,
            'color': region.color,
            'uv_start': Vector2(
                region.position.x / self.texture_size.x,
                region.position.y / self.texture_size.y,
            ),
            'uv_end': Vector2(
                (region.position.x + region.size.x) / self.texture_size.x,
                (region.position.y + region.size.y) / self.texture_size.y,
            ),
            'region': region,
        }
        self._frames.pop(name, None)

    def get_sprite_data(self, name: str) -> Optional[Dict]:
        """Return metadata for a named region."""
        data = self.sprites.get(name)
        if data is None:
            return None
        result = data.copy()
        result['image'] = self.get_frame(name) if self.image is not None else None
        return result

    def get_frame(self, name: str):
        """Return a cached extracted frame for a named region."""
        if name not in self.sprites:
            raise KeyError(f"Unknown sprite region: '{name}'")
        if self.image is None:
            return None
        if name not in self._frames:
            region = self.sprites[name]['region']
            self._frames[name] = self._frame_factory(self.image, region)
        return self._frames[name]

    def clear_frames(self):
        """Release all extracted frame references while keeping region data."""
        self._frames.clear()

    def create_animation_frames(
        self,
        base_name: str,
        frame_count: int,
        frame_size: Vector2,
        start_position: Vector2,
        horizontal: bool = True,
    ) -> List[str]:
        """Add evenly spaced horizontal or vertical animation regions."""
        if frame_count <= 0:
            raise ValueError("frame_count must be greater than zero")

        frame_names = []
        for index in range(frame_count):
            frame_name = f"{base_name}_frame_{index}"
            if horizontal:
                frame_position = Vector2(
                    start_position.x + index * frame_size.x,
                    start_position.y,
                )
            else:
                frame_position = Vector2(
                    start_position.x,
                    start_position.y + index * frame_size.y,
                )
            self.add_sprite(frame_name, frame_position, frame_size)
            frame_names.append(frame_name)
        return frame_names

    def _validate_region(self, name: str, position: Vector2, size: Vector2):
        if not name:
            raise ValueError("sprite name cannot be empty")
        if position.x < 0 or position.y < 0:
            raise ValueError("sprite position cannot be negative")
        if size.x <= 0 or size.y <= 0:
            raise ValueError("sprite size components must be greater than zero")
        if position.x + size.x > self.texture_size.x:
            raise ValueError(f"sprite '{name}' exceeds atlas width")
        if position.y + size.y > self.texture_size.y:
            raise ValueError(f"sprite '{name}' exceeds atlas height")
        for value in (position.x, position.y, size.x, size.y):
            if not float(value).is_integer():
                raise ValueError("sprite-sheet coordinates must be whole pixels")

    @staticmethod
    def _extract_photo_image(source, region: AtlasRegion):
        width = int(region.size.x)
        height = int(region.size.y)
        x = int(region.position.x)
        y = int(region.position.y)
        frame = tk.PhotoImage(width=width, height=height)
        frame.tk.call(
            str(frame),
            'copy',
            str(source),
            '-from',
            x,
            y,
            x + width,
            y + height,
            '-to',
            0,
            0,
        )
        return frame
