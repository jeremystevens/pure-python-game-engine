"""Reusable animation clips and independent playback state."""

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple, Union


FrameKey = Union[str, int]
CompletionCallback = Callable[[], None]


@dataclass(frozen=True)
class AnimationClip:
    """Immutable frame sequence that can be shared by multiple sprites."""

    name: str
    frames: Tuple[FrameKey, ...]
    frame_duration: float = 0.1
    loop: bool = True

    def __post_init__(self):
        object.__setattr__(self, 'frames', tuple(self.frames))
        if not self.name:
            raise ValueError("animation name cannot be empty")
        if not self.frames:
            raise ValueError("animation must contain at least one frame")
        if self.frame_duration <= 0:
            raise ValueError("frame_duration must be greater than zero")

    @classmethod
    def from_frames(
        cls,
        name: str,
        frames: Sequence[FrameKey],
        frame_duration: float = 0.1,
        loop: bool = True,
    ) -> 'AnimationClip':
        """Create a clip while copying its frame sequence."""
        return cls(name, tuple(frames), frame_duration, loop)


class SpriteAnimation:
    """Playback state for an AnimationClip."""

    def __init__(
        self,
        name: str,
        frame_indices: Sequence[FrameKey],
        frame_duration: float = 0.1,
        loop: bool = True,
        on_complete: Optional[CompletionCallback] = None,
    ):
        self.clip = AnimationClip.from_frames(
            name,
            frame_indices,
            frame_duration,
            loop,
        )
        self.on_complete = on_complete
        self.current_frame = 0
        self.frame_timer = 0.0
        self.is_playing = False
        self.is_finished = False

    @classmethod
    def from_clip(
        cls,
        clip: AnimationClip,
        on_complete: Optional[CompletionCallback] = None,
    ) -> 'SpriteAnimation':
        """Create independent playback state for a shared clip."""
        animation = cls.__new__(cls)
        animation.clip = clip
        animation.on_complete = on_complete
        animation.current_frame = 0
        animation.frame_timer = 0.0
        animation.is_playing = False
        animation.is_finished = False
        return animation

    @property
    def name(self) -> str:
        return self.clip.name

    @property
    def frame_indices(self) -> Tuple[FrameKey, ...]:
        return self.clip.frames

    @property
    def frame_duration(self) -> float:
        return self.clip.frame_duration

    @property
    def loop(self) -> bool:
        return self.clip.loop

    @property
    def current_frame_key(self) -> FrameKey:
        return self.clip.frames[self.current_frame]

    def update(self, delta_time: float) -> FrameKey:
        """Advance playback by elapsed seconds and return the active frame."""
        if delta_time < 0:
            raise ValueError("delta_time cannot be negative")
        if not self.is_playing:
            return self.current_frame_key

        self.frame_timer += delta_time
        epsilon = 1e-12
        while (
            self.frame_timer + epsilon >= self.frame_duration
            and self.is_playing
        ):
            self.frame_timer = max(0.0, self.frame_timer - self.frame_duration)
            self._advance_frame()

        return self.current_frame_key

    def _advance_frame(self):
        next_frame = self.current_frame + 1
        if next_frame < len(self.frame_indices):
            self.current_frame = next_frame
            return

        if self.loop:
            self.current_frame = 0
            if self.on_complete:
                self.on_complete()
            return

        self.current_frame = len(self.frame_indices) - 1
        self.frame_timer = 0.0
        self.is_playing = False
        self.is_finished = True
        if self.on_complete:
            self.on_complete()

    def play(self, reset: bool = False):
        """Start or resume playback, optionally restarting at frame zero."""
        if reset or self.is_finished:
            self.reset()
        self.is_playing = True

    def pause(self):
        """Pause without changing the active frame or accumulated time."""
        self.is_playing = False

    def resume(self):
        """Resume paused playback."""
        self.play()

    def stop(self):
        """Stop playback and reset to the first frame."""
        self.reset()

    def reset(self):
        """Reset playback without starting it."""
        self.current_frame = 0
        self.frame_timer = 0.0
        self.is_playing = False
        self.is_finished = False
