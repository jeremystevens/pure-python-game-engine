"""Scene lifecycle, object management, rendering, and collision integration."""

from typing import Any, Dict, List, Optional

from ..graphics.renderer import Renderer
from .game_object import GameObject


class Scene:
    """Organize GameObjects with deterministic lifecycle and mutation points."""

    def __init__(self, name: str = "Untitled Scene"):
        # Imported lazily: engine.collision depends on Component from this
        # package, so importing CollisionSystem at module level here would
        # create a circular import depending on which package loads first.
        from ..collision.system import CollisionSystem

        self.name = name
        self.game_objects: List[GameObject] = []
        self.objects_by_name: Dict[str, GameObject] = {}
        self.objects_by_tag: Dict[str, List[GameObject]] = {}
        self.is_active = True
        self.is_initialized = False
        self.is_paused = False
        self.data: Dict[str, Any] = {}
        self.collision_system = CollisionSystem(self)
        self._is_updating = False
        self._pending_additions: List[GameObject] = []
        self._pending_removals: List[GameObject] = []

    def initialize(self) -> bool:
        """Initialize this scene and start its objects exactly once."""
        if self.is_initialized:
            return False
        self.is_initialized = True
        self.is_active = True
        self.is_paused = False
        self.on_initialize()
        for game_object in tuple(self.game_objects):
            game_object._ensure_started()
        return True

    def on_initialize(self):
        """Override to populate or otherwise initialize this scene."""
        pass

    def pause(self) -> bool:
        """Pause updates while keeping this scene renderable."""
        if not self.is_initialized or self.is_paused:
            return False
        self.is_paused = True
        self.on_pause()
        return True

    def on_pause(self):
        """Override to respond to this scene being covered on a stack."""
        pass

    def resume(self) -> bool:
        """Resume updates after this scene returns to the top of a stack."""
        if not self.is_initialized or not self.is_paused:
            return False
        self.is_paused = False
        self.on_resume()
        return True

    def on_resume(self):
        """Override to respond to this scene returning to the stack top."""
        pass

    def add_object(self, game_object: GameObject) -> GameObject:
        """Add an object now or defer it until the current update completes."""
        if game_object in self.game_objects or game_object in self._pending_additions:
            return game_object
        if game_object.scene is not None and game_object.scene is not self:
            raise ValueError(
                f"GameObject '{game_object.name}' already belongs to another scene"
            )
        if game_object in self._pending_removals:
            self._pending_removals.remove(game_object)
            return game_object
        if self._is_updating:
            self._pending_additions.append(game_object)
        else:
            self._attach_object(game_object)
        return game_object

    def remove_object(self, game_object: GameObject) -> bool:
        """Remove an object now or defer removal until update completion."""
        if game_object in self._pending_additions:
            self._pending_additions.remove(game_object)
            return True
        if game_object not in self.game_objects:
            return False
        if self._is_updating:
            if game_object not in self._pending_removals:
                self._pending_removals.append(game_object)
        else:
            self._detach_object(game_object)
        return True

    def is_object_pending_removal(self, game_object: GameObject) -> bool:
        """Return whether an object will leave at the end of this update."""
        return game_object in self._pending_removals

    def _attach_object(self, game_object: GameObject):
        existing = self.objects_by_name.get(game_object.name)
        if (
            existing is not None
            and existing is not game_object
            and (existing.is_persistent or game_object.is_persistent)
        ):
            raise ValueError(
                f"Persistent object name conflict: '{game_object.name}'"
            )
        self.game_objects.append(game_object)
        game_object.scene = self
        self._index_object(game_object)
        if self.is_initialized:
            game_object._ensure_started()

    def _detach_object(self, game_object: GameObject):
        if game_object not in self.game_objects:
            return
        self.game_objects.remove(game_object)
        self._unindex_object(game_object)
        game_object.scene = None

    def _index_object(self, game_object: GameObject):
        if game_object.name:
            self.objects_by_name[game_object.name] = game_object
        for tag in game_object.tags:
            tagged_objects = self.objects_by_tag.setdefault(tag, [])
            if game_object not in tagged_objects:
                tagged_objects.append(game_object)

    def _unindex_object(self, game_object: GameObject):
        if self.objects_by_name.get(game_object.name) is game_object:
            self.objects_by_name.pop(game_object.name, None)
            for candidate in reversed(self.game_objects):
                if candidate.name == game_object.name:
                    self.objects_by_name[game_object.name] = candidate
                    break
        for tag in tuple(game_object.tags):
            tagged_objects = self.objects_by_tag.get(tag)
            if not tagged_objects:
                continue
            if game_object in tagged_objects:
                tagged_objects.remove(game_object)
            if not tagged_objects:
                del self.objects_by_tag[tag]

    def find_object(self, name: str) -> Optional[GameObject]:
        """Find the most recently added object with this name."""
        return self.objects_by_name.get(name)

    def find_objects_with_tag(self, tag: str) -> List[GameObject]:
        """Find all current objects with this tag."""
        return self.objects_by_tag.get(tag, []).copy()

    def find_objects_of_type(self, object_type: type) -> List[GameObject]:
        """Find all current objects matching a type."""
        return [
            game_object
            for game_object in self.game_objects
            if isinstance(game_object, object_type)
        ]

    def update(self, delta_time: float):
        """Update a stable object snapshot and then apply queued mutations."""
        if not self.is_active:
            return
        if not self.is_initialized:
            self.initialize()
        if self.is_paused:
            return

        self._is_updating = True
        try:
            for game_object in tuple(self.game_objects):
                if (
                    game_object.is_active
                    and not game_object.is_destroyed
                    and game_object not in self._pending_removals
                ):
                    game_object.update(delta_time)

            self.collision_system.update()
            for game_object in tuple(self.game_objects):
                if game_object.is_destroyed:
                    self.remove_object(game_object)
        finally:
            self._is_updating = False
            self._flush_pending_mutations()

    def _flush_pending_mutations(self):
        pending_removals = tuple(self._pending_removals)
        pending_additions = tuple(self._pending_additions)
        self._pending_removals.clear()
        self._pending_additions.clear()

        for game_object in pending_removals:
            self._detach_object(game_object)
        for game_object in pending_additions:
            if not game_object.is_destroyed and game_object not in self.game_objects:
                self._attach_object(game_object)

    def render(self, renderer: Renderer):
        """Render active objects in z-order, including while paused."""
        if not self.is_active:
            return
        sorted_objects = sorted(
            (
                game_object
                for game_object in self.game_objects
                if game_object.is_active and not game_object.is_destroyed
            ),
            key=lambda game_object: game_object.z_order,
        )
        for game_object in sorted_objects:
            game_object.render(renderer)

    def extract_persistent_objects(self) -> List[GameObject]:
        """Detach and return objects marked to survive scene replacement."""
        if self._is_updating:
            raise RuntimeError("cannot transfer persistent objects during update")
        self._flush_pending_mutations()
        persistent_objects = [
            game_object
            for game_object in tuple(self.game_objects)
            if game_object.is_persistent and not game_object.is_destroyed
        ]
        for game_object in persistent_objects:
            self._detach_object(game_object)
        return persistent_objects

    def cleanup(self) -> bool:
        """Destroy this scene once and release all object and collision state."""
        if not self.is_initialized and not self.game_objects:
            return False
        if self._is_updating:
            raise RuntimeError("cannot clean up a scene during update")

        self._flush_pending_mutations()
        self.collision_system.clear()
        if self.is_initialized:
            self.on_cleanup()
        for game_object in tuple(self.game_objects):
            game_object.destroy()
            game_object.scene = None
        self.game_objects.clear()
        self.objects_by_name.clear()
        self.objects_by_tag.clear()
        self._pending_additions.clear()
        self._pending_removals.clear()
        self.is_initialized = False
        self.is_paused = False
        self.is_active = False
        return True

    def on_cleanup(self):
        """Override to release custom scene resources before object teardown."""
        pass

    def set_active(self, active: bool):
        """Enable or disable both scene update and rendering."""
        self.is_active = active

    def get_object_count(self) -> int:
        """Return the number of attached objects."""
        return len(self.game_objects)

    def get_active_object_count(self) -> int:
        """Return the number of active, non-destroyed objects."""
        return len(
            [
                game_object
                for game_object in self.game_objects
                if game_object.is_active and not game_object.is_destroyed
            ]
        )
