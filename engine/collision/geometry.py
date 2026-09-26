"""Geometry primitives and intersection tests for 2D collision detection."""

from dataclasses import dataclass
from typing import Union

from ..math.vector2 import Vector2


@dataclass(frozen=True)
class Circle:
    """A circle defined by its center and radius."""

    center: Vector2
    radius: float

    def __post_init__(self):
        if self.radius < 0:
            raise ValueError("radius cannot be negative")


@dataclass(frozen=True)
class AABB:
    """An axis-aligned bounding box defined by its center and half-size."""

    center: Vector2
    half_size: Vector2

    def __post_init__(self):
        if self.half_size.x < 0 or self.half_size.y < 0:
            raise ValueError("half_size components cannot be negative")

    @classmethod
    def from_size(cls, center: Vector2, size: Vector2) -> 'AABB':
        """Create a box from its center and full width and height."""
        return cls(center, Vector2(size.x / 2, size.y / 2))

    @property
    def minimum(self) -> Vector2:
        """Return the minimum corner."""
        return self.center - self.half_size

    @property
    def maximum(self) -> Vector2:
        """Return the maximum corner."""
        return self.center + self.half_size


Shape = Union[Circle, AABB]


def point_in_circle(point: Vector2, circle: Circle) -> bool:
    """Return whether a point is inside or on a circle."""
    return point.distance_squared_to(circle.center) <= circle.radius * circle.radius


def point_in_aabb(point: Vector2, box: AABB) -> bool:
    """Return whether a point is inside or on an axis-aligned box."""
    minimum = box.minimum
    maximum = box.maximum
    return minimum.x <= point.x <= maximum.x and minimum.y <= point.y <= maximum.y


def circles_intersect(first: Circle, second: Circle) -> bool:
    """Return whether two circles overlap or touch."""
    combined_radius = first.radius + second.radius
    return (
        first.center.distance_squared_to(second.center)
        <= combined_radius * combined_radius
    )


def aabbs_intersect(first: AABB, second: AABB) -> bool:
    """Return whether two axis-aligned boxes overlap or touch."""
    return (
        abs(first.center.x - second.center.x)
        <= first.half_size.x + second.half_size.x
        and abs(first.center.y - second.center.y)
        <= first.half_size.y + second.half_size.y
    )


def circle_intersects_aabb(circle: Circle, box: AABB) -> bool:
    """Return whether a circle overlaps or touches an axis-aligned box."""
    minimum = box.minimum
    maximum = box.maximum
    nearest_x = max(minimum.x, min(circle.center.x, maximum.x))
    nearest_y = max(minimum.y, min(circle.center.y, maximum.y))
    nearest = Vector2(nearest_x, nearest_y)
    return point_in_circle(nearest, circle)


def shapes_intersect(first: Shape, second: Shape) -> bool:
    """Dispatch an intersection test for any supported shape pair."""
    if isinstance(first, Circle) and isinstance(second, Circle):
        return circles_intersect(first, second)
    if isinstance(first, AABB) and isinstance(second, AABB):
        return aabbs_intersect(first, second)
    if isinstance(first, Circle) and isinstance(second, AABB):
        return circle_intersects_aabb(first, second)
    if isinstance(first, AABB) and isinstance(second, Circle):
        return circle_intersects_aabb(second, first)
    raise TypeError(
        f"Unsupported shape pair: {type(first).__name__}, {type(second).__name__}"
    )
