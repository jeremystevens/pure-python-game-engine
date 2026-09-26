"""Scene-level collision detection and contact lifecycle management."""

from itertools import combinations
from typing import Dict, List, Tuple, TYPE_CHECKING

from .collider import Collider
from .geometry import shapes_intersect

if TYPE_CHECKING:
    from ..scene.scene import Scene


CollisionPair = Tuple[Collider, Collider]
CollisionPairKey = Tuple[int, int]


class CollisionSystem:
    """Detect overlaps and dispatch enter, stay, and exit callbacks."""

    def __init__(self, scene: 'Scene'):
        self.scene = scene
        self._active_pairs: Dict[CollisionPairKey, CollisionPair] = {}

    @property
    def active_pair_count(self) -> int:
        """Return the number of contacts active after the latest update."""
        return len(self._active_pairs)

    def update(self):
        """Detect contacts using a stable snapshot of the scene's colliders."""
        colliders = self._collect_colliders()
        current_pairs: Dict[CollisionPairKey, CollisionPair] = {}

        for first, second in combinations(colliders, 2):
            if first.game_object is second.game_object:
                continue
            if not first.can_collide_with(second):
                continue
            if not shapes_intersect(first.shape, second.shape):
                continue

            key = self._pair_key(first, second)
            current_pairs[key] = (first, second)
            if key in self._active_pairs:
                self._emit_pair('stay', first, second)
            else:
                self._emit_pair('enter', first, second)

        for key, pair in tuple(self._active_pairs.items()):
            if key not in current_pairs:
                self._emit_pair('exit', *pair)

        self._active_pairs = current_pairs

    def clear(self):
        """Discard all active contacts without emitting callbacks."""
        self._active_pairs.clear()

    def _collect_colliders(self) -> List[Collider]:
        colliders = []
        for game_object in tuple(self.scene.game_objects):
            if not game_object.is_active or game_object.is_destroyed:
                continue
            for component in tuple(game_object.components_list):
                if isinstance(component, Collider) and component.is_active:
                    colliders.append(component)
        return colliders

    def _emit_pair(self, event: str, first: Collider, second: Collider):
        first_handler = getattr(first, f'_emit_{event}')
        second_handler = getattr(second, f'_emit_{event}')

        if self._can_receive_event(first):
            first_handler(second)
        if self._can_receive_event(second):
            second_handler(first)

    def _can_receive_event(self, collider: Collider) -> bool:
        game_object = collider.game_object
        return bool(
            collider.is_active
            and game_object
            and game_object.is_active
            and not game_object.is_destroyed
            and game_object.scene is self.scene
        )

    @staticmethod
    def _pair_key(first: Collider, second: Collider) -> CollisionPairKey:
        first_id = id(first)
        second_id = id(second)
        return (
            (first_id, second_id)
            if first_id < second_id
            else (second_id, first_id)
        )
