"""2D collision geometry, collider components, and scene integration."""

from .collider import AABBCollider, CircleCollider, Collider, PointCollider
from .geometry import (
    AABB,
    Circle,
    aabbs_intersect,
    circle_intersects_aabb,
    circles_intersect,
    point_in_aabb,
    point_in_circle,
    shapes_intersect,
)
from .system import CollisionSystem

__all__ = [
    'AABB',
    'Circle',
    'Collider',
    'PointCollider',
    'CircleCollider',
    'AABBCollider',
    'CollisionSystem',
    'point_in_circle',
    'point_in_aabb',
    'circles_intersect',
    'aabbs_intersect',
    'circle_intersects_aabb',
    'shapes_intersect',
]
