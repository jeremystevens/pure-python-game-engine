"""GameObject collider components."""

from typing import Callable, List, Optional

from ..math.vector2 import Vector2
from ..scene.game_object import Component
from .geometry import AABB, Circle, Shape, point_in_aabb, point_in_circle


CollisionCallback = Callable[['Collider'], None]


class Collider(Component):
    """Base component for non-physical overlap detection."""

    ALL_LAYERS = (1 << 32) - 1

    def __init__(
        self,
        offset: Optional[Vector2] = None,
        layer: int = 1,
        mask: int = ALL_LAYERS,
    ):
        super().__init__()
        if layer < 0 or mask < 0:
            raise ValueError("layer and mask cannot be negative")

        self.offset = offset.copy() if offset else Vector2.zero()
        self.layer = layer
        self.mask = mask
        self._enter_callbacks: List[CollisionCallback] = []
        self._stay_callbacks: List[CollisionCallback] = []
        self._exit_callbacks: List[CollisionCallback] = []

    @property
    def world_center(self) -> Vector2:
        """Return the collider center after applying the GameObject transform."""
        if not self.game_object:
            return self.offset.copy()
        return self.game_object.transform.transform_point(self.offset)

    @property
    def shape(self) -> Shape:
        """Return the collider's current world-space geometry."""
        raise NotImplementedError

    def contains_point(self, point: Vector2) -> bool:
        """Return whether the world-space point is inside this collider."""
        shape = self.shape
        if isinstance(shape, Circle):
            return point_in_circle(point, shape)
        return point_in_aabb(point, shape)

    def can_collide_with(self, other: 'Collider') -> bool:
        """Return whether both colliders' layer and mask settings allow contact."""
        return bool(self.mask & other.layer) and bool(other.mask & self.layer)

    def on_enter(self, callback: CollisionCallback) -> CollisionCallback:
        """Register a callback for the first frame of contact."""
        self._enter_callbacks.append(callback)
        return callback

    def on_stay(self, callback: CollisionCallback) -> CollisionCallback:
        """Register a callback for each additional frame of contact."""
        self._stay_callbacks.append(callback)
        return callback

    def on_exit(self, callback: CollisionCallback) -> CollisionCallback:
        """Register a callback for the frame after contact ends."""
        self._exit_callbacks.append(callback)
        return callback

    def remove_enter_callback(self, callback: CollisionCallback) -> bool:
        """Remove an enter callback if it is registered."""
        return self._remove_callback(self._enter_callbacks, callback)

    def remove_stay_callback(self, callback: CollisionCallback) -> bool:
        """Remove a stay callback if it is registered."""
        return self._remove_callback(self._stay_callbacks, callback)

    def remove_exit_callback(self, callback: CollisionCallback) -> bool:
        """Remove an exit callback if it is registered."""
        return self._remove_callback(self._exit_callbacks, callback)

    def _remove_callback(
        self,
        callbacks: List[CollisionCallback],
        callback: CollisionCallback,
    ) -> bool:
        if callback not in callbacks:
            return False
        callbacks.remove(callback)
        return True

    def _emit_enter(self, other: 'Collider'):
        for callback in tuple(self._enter_callbacks):
            callback(other)

    def _emit_stay(self, other: 'Collider'):
        for callback in tuple(self._stay_callbacks):
            callback(other)

    def _emit_exit(self, other: 'Collider'):
        for callback in tuple(self._exit_callbacks):
            callback(other)


class PointCollider(Collider):
    """Point collider positioned by a GameObject transform and local offset."""

    @property
    def shape(self) -> Circle:
        return Circle(self.world_center, 0.0)


class CircleCollider(Collider):
    """Circular collider centered on a GameObject transform."""

    def __init__(
        self,
        radius: float,
        offset: Optional[Vector2] = None,
        layer: int = 1,
        mask: int = Collider.ALL_LAYERS,
    ):
        if radius < 0:
            raise ValueError("radius cannot be negative")
        super().__init__(offset, layer, mask)
        self.radius = radius

    @property
    def shape(self) -> Circle:
        scale = Vector2.one()
        if self.game_object:
            scale = self.game_object.transform.world_scale
        world_radius = self.radius * max(abs(scale.x), abs(scale.y))
        return Circle(self.world_center, world_radius)


class AABBCollider(Collider):
    """Axis-aligned rectangular collider centered on a GameObject transform."""

    def __init__(
        self,
        size: Vector2,
        offset: Optional[Vector2] = None,
        layer: int = 1,
        mask: int = Collider.ALL_LAYERS,
    ):
        if size.x < 0 or size.y < 0:
            raise ValueError("size components cannot be negative")
        super().__init__(offset, layer, mask)
        self.size = size.copy()

    @property
    def shape(self) -> AABB:
        scale = Vector2.one()
        if self.game_object:
            scale = self.game_object.transform.world_scale
        world_size = Vector2(
            self.size.x * abs(scale.x),
            self.size.y * abs(scale.y),
        )
        return AABB.from_size(self.world_center, world_size)
