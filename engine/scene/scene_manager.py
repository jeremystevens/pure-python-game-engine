"""Named scene registry, stack transitions, and persistent-object transfer."""

from collections import deque
from typing import Callable, Deque, Dict, List, Optional, Tuple, Union

from .scene import Scene


SceneFactory = Callable[[], Scene]
SceneProvider = Union[Scene, SceneFactory]
SceneTarget = Union[str, Scene]
Transition = Tuple[str, Optional[SceneTarget]]


class SceneManager:
    """Manage named scenes and deferred stack transitions."""

    def __init__(self, engine=None, initial_scene: Optional[Scene] = None):
        self.engine = engine
        self._registry: Dict[str, SceneProvider] = {}
        self._stack: List[Scene] = []
        self._pending: Deque[Transition] = deque()
        if initial_scene is not None:
            self._stack.append(initial_scene)
            self._attach_engine(initial_scene)

    @property
    def current_scene(self) -> Optional[Scene]:
        """Return the scene at the top of the stack."""
        return self._stack[-1] if self._stack else None

    @property
    def stack_depth(self) -> int:
        """Return the number of active stacked scenes."""
        return len(self._stack)

    @property
    def scene_stack(self) -> Tuple[Scene, ...]:
        """Return an immutable bottom-to-top stack snapshot."""
        return tuple(self._stack)

    @property
    def registered_scene_names(self) -> Tuple[str, ...]:
        """Return registered names in insertion order."""
        return tuple(self._registry)

    @property
    def has_pending_transition(self) -> bool:
        return bool(self._pending)

    def register(
        self,
        name: str,
        provider: SceneProvider,
        replace: bool = False,
    ):
        """Register a Scene instance or zero-argument Scene factory."""
        if not name:
            raise ValueError("scene name cannot be empty")
        if name in self._registry and not replace:
            raise ValueError(f"Scene '{name}' is already registered")
        if not isinstance(provider, Scene) and not callable(provider):
            raise TypeError("scene provider must be a Scene or callable factory")
        self._registry[name] = provider

    def unregister(self, name: str) -> bool:
        """Remove a named provider from the registry."""
        if name not in self._registry:
            return False
        del self._registry[name]
        return True

    def set_initial(self, scene: Scene):
        """Set an uninitialized current scene before the engine starts."""
        current = self.current_scene
        if current is not None and getattr(current, 'is_initialized', False):
            self.replace_now(scene)
            return
        self._stack = [scene]
        self._attach_engine(scene)

    def initialize_current(self):
        """Initialize the current scene if one exists."""
        if self.current_scene:
            self.current_scene.initialize()

    def replace(self, target: SceneTarget):
        """Queue replacement of the current scene."""
        self._pending.append(('replace', target))

    def push(self, target: SceneTarget):
        """Queue a scene overlay push."""
        self._pending.append(('push', target))

    def pop(self):
        """Queue removal of the top scene."""
        self._pending.append(('pop', None))

    def process_pending(self):
        """Apply all transitions queued before this synchronization point."""
        while self._pending:
            operation, target = self._pending.popleft()
            if operation == 'replace':
                self.replace_now(target)
            elif operation == 'push':
                self.push_now(target)
            else:
                self.pop_now()

    def replace_now(self, target: SceneTarget) -> Scene:
        """Replace the top scene and transfer persistent objects."""
        new_scene = self._resolve(target)
        old_scene = self.current_scene
        if new_scene is old_scene:
            return new_scene

        persistent_objects = []
        if old_scene is not None:
            persistent_objects = self._validated_persistent_objects(
                old_scene,
                new_scene,
            )
            if hasattr(old_scene, 'extract_persistent_objects'):
                persistent_objects = old_scene.extract_persistent_objects()
            old_scene.cleanup()

        if self._stack:
            self._stack[-1] = new_scene
        else:
            self._stack.append(new_scene)

        self._attach_engine(new_scene)
        for game_object in persistent_objects:
            new_scene.add_object(game_object)
        try:
            new_scene.initialize()
        except BaseException:
            new_scene.cleanup()
            raise
        return new_scene

    def push_now(self, target: SceneTarget) -> Scene:
        """Pause the current scene and push an initialized overlay."""
        scene = self._resolve(target)
        if scene in self._stack:
            raise ValueError("cannot push a scene already present in the stack")
        current = self.current_scene
        if current is not None and hasattr(current, 'pause'):
            current.pause()
        self._attach_engine(scene)
        try:
            scene.initialize()
        except BaseException:
            if current is not None and hasattr(current, 'resume'):
                current.resume()
            raise
        self._stack.append(scene)
        return scene

    def pop_now(self) -> Optional[Scene]:
        """Clean the top scene and resume the one beneath it."""
        if len(self._stack) <= 1:
            return None
        removed = self._stack.pop()
        removed.cleanup()
        current = self.current_scene
        if current is not None and hasattr(current, 'resume'):
            current.resume()
        return removed

    def update(self, delta_time: float):
        """Update only the top scene."""
        if self.current_scene:
            self.current_scene.update(delta_time)

    def render(self, renderer):
        """Render stacked scenes from bottom to top."""
        for scene in tuple(self._stack):
            scene.render(renderer)

    def clear(self):
        """Clean every stacked scene from top to bottom."""
        self._pending.clear()
        while self._stack:
            scene = self._stack.pop()
            scene.cleanup()

    def _resolve(self, target: SceneTarget) -> Scene:
        if isinstance(target, str):
            if target not in self._registry:
                raise KeyError(f"Unknown scene: '{target}'")
            provider = self._registry[target]
            scene = provider() if callable(provider) else provider
        else:
            scene = target
        if not isinstance(scene, Scene):
            raise TypeError("scene provider must return a Scene")
        return scene

    def _attach_engine(self, scene: Scene):
        if self.engine is not None:
            scene.engine = self.engine

    def _validated_persistent_objects(
        self,
        old_scene: Scene,
        new_scene: Scene,
    ) -> List:
        persistent_objects = [
            game_object
            for game_object in getattr(old_scene, 'game_objects', ())
            if getattr(game_object, 'is_persistent', False)
            and not getattr(game_object, 'is_destroyed', False)
        ]
        names = [game_object.name for game_object in persistent_objects]
        if any(not name for name in names) or len(names) != len(set(names)):
            new_scene.cleanup()
            raise ValueError("persistent objects must have unique non-empty names")
        for game_object in persistent_objects:
            if game_object.name and new_scene.find_object(game_object.name):
                new_scene.cleanup()
                raise ValueError(
                    f"Persistent object name conflicts with target scene: "
                    f"'{game_object.name}'"
                )
        return persistent_objects
