"""Runtime debugging tools: a stats overlay, collider visualization, cyclable
log-level control, and console scene inspection, all behind function-key toggles."""

from typing import List, Optional, Tuple

from ..collision.collider import Collider
from ..collision.geometry import Circle
from ..core.logger import LogLevel, get_logger, set_global_log_level
from ..math.vector2 import Vector2


_LOG_LEVEL_CYCLE = (LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR)


class DebugOverlay:
    """Optional, engine-owned debugging tools toggled by function keys.

    F3 stats overlay | F4 collider outlines | F5 cycle log level | F6 inspect scene
    """

    SLOW_FRAME_MULTIPLIER = 2.0
    FRAME_HISTORY_SIZE = 120

    def __init__(self, engine):
        self.engine = engine
        self.logger = get_logger('Debug')
        self.stats_visible = False
        self.colliders_visible = False
        self._log_level_index = _LOG_LEVEL_CYCLE.index(LogLevel.INFO)
        self._frame_times_seconds: List[float] = []

    @property
    def log_level(self) -> LogLevel:
        """Return the log level the F5 cycle is currently set to."""
        return _LOG_LEVEL_CYCLE[self._log_level_index]

    def handle_input(self, input_manager):
        """Check debug hotkeys. Call once per frame, before game update logic."""
        if input_manager.is_key_just_pressed('f3'):
            self.stats_visible = not self.stats_visible
        if input_manager.is_key_just_pressed('f4'):
            self.colliders_visible = not self.colliders_visible
        if input_manager.is_key_just_pressed('f5'):
            self._cycle_log_level()
        if input_manager.is_key_just_pressed('f6'):
            self.dump_scene(self.engine.current_scene)

    def _cycle_log_level(self):
        self._log_level_index = (self._log_level_index + 1) % len(_LOG_LEVEL_CYCLE)
        set_global_log_level(self.log_level)
        # Logged at the new level itself, since it always passes its own
        # threshold -- e.g. logging this at .info() would silently vanish
        # the moment the level is raised above INFO.
        self.logger.log(self.log_level, f"Log level set to {self.log_level.name}")

    def record_frame(self, raw_delta_time: float):
        """Track a real (unbounded) frame duration and warn if it was slow.

        Uses the window's raw delta rather than the engine's smoothed,
        stall-capped delta_time, since profiling needs the true frame cost.
        """
        self._frame_times_seconds.append(raw_delta_time)
        if len(self._frame_times_seconds) > self.FRAME_HISTORY_SIZE:
            self._frame_times_seconds.pop(0)

        target_frame_time = 1.0 / self.engine.target_fps
        if raw_delta_time > target_frame_time * self.SLOW_FRAME_MULTIPLIER:
            self.logger.warning(
                f"Slow frame: {raw_delta_time * 1000:.1f}ms "
                f"(target {target_frame_time * 1000:.1f}ms)"
            )

    def frame_time_stats_ms(self) -> Tuple[float, float, float]:
        """Return (average, minimum, maximum) recorded frame time in milliseconds."""
        if not self._frame_times_seconds:
            return (0.0, 0.0, 0.0)
        times_ms = [seconds * 1000 for seconds in self._frame_times_seconds]
        return (sum(times_ms) / len(times_ms), min(times_ms), max(times_ms))

    def collect_colliders(self, scene) -> List[Collider]:
        """Return every active collider on an active, non-destroyed object."""
        if scene is None:
            return []
        colliders = []
        for game_object in scene.game_objects:
            if not game_object.is_active or game_object.is_destroyed:
                continue
            for component in game_object.components_list:
                if isinstance(component, Collider) and component.is_active:
                    colliders.append(component)
        return colliders

    def dump_scene(self, scene) -> int:
        """Log a snapshot of every object in a scene. Returns the object count."""
        if scene is None:
            self.logger.info("No active scene to inspect")
            return 0

        game_objects = scene.game_objects
        self.logger.info(
            f"Scene '{scene.name}': {len(game_objects)} object(s), "
            f"{scene.get_active_object_count()} active"
        )
        for game_object in game_objects:
            component_names = [type(c).__name__ for c in game_object.components_list]
            position = game_object.transform.position
            self.logger.info(
                f"  {game_object.name!r} pos=({position.x:.1f}, {position.y:.1f}) "
                f"active={game_object.is_active} tags={game_object.tags} "
                f"components={component_names}"
            )
        return len(game_objects)

    def render(self, renderer, scene: Optional[object]):
        """Draw whichever debug visuals are currently enabled, on top of everything."""
        if self.colliders_visible:
            self._render_colliders(renderer, scene)
        if self.stats_visible:
            self._render_stats(renderer, scene)

    def _render_colliders(self, renderer, scene):
        for collider in self.collect_colliders(scene):
            shape = collider.shape
            if isinstance(shape, Circle):
                radius = max(shape.radius, 1.0)
                renderer.draw_circle(shape.center, radius, color='', outline='#00FF00', width=1)
            else:
                size = Vector2(shape.half_size.x * 2, shape.half_size.y * 2)
                renderer.draw_rectangle(shape.center, size, color='', outline='#00FF00', width=1)

    def _render_stats(self, renderer, scene):
        average_ms, minimum_ms, maximum_ms = self.frame_time_stats_ms()
        object_count = len(scene.game_objects) if scene else 0
        active_count = scene.get_active_object_count() if scene else 0
        collider_count = len(self.collect_colliders(scene))
        scene_name = scene.name if scene else 'None'

        lines = [
            f"FPS: {self.engine.get_fps():.1f}   Frame: {average_ms:.1f}ms "
            f"(min {minimum_ms:.1f} / max {maximum_ms:.1f})",
            f"Scene: {scene_name}   Stack depth: {self.engine.scene_manager.stack_depth}",
            f"Objects: {object_count} ({active_count} active)   Colliders: {collider_count}",
            f"Log level: {self.log_level.name}",
            "F3 stats  F4 colliders  F5 log level  F6 inspect scene",
        ]

        y = 10
        for line in lines:
            renderer.draw_text(Vector2(10, y), line, '#00FF00', 12, 'nw')
            y += 16
