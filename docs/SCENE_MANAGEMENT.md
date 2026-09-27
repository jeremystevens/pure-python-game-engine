# Scene Management

The engine provides a `Scene` lifecycle with deterministic mutation points, plus a `SceneManager` that adds a named scene registry and a scene stack for menus, dialogs, and pause overlays. No external dependencies are involved.

## Scene Lifecycle

Every `Scene` exposes idempotent public entry points and matching `on_*` hooks for subclasses to override:

```python
from engine import Scene

class MenuScene(Scene):
    def on_initialize(self):
        """Populate the scene. Runs exactly once."""

    def on_pause(self):
        """Called when this scene is covered by a pushed overlay."""

    def on_resume(self):
        """Called when this scene returns to the top of the stack."""

    def on_cleanup(self):
        """Release custom resources before objects are destroyed."""
```

- `initialize()` returns `True` the first time it runs and `False` on any later call — calling it again is always safe.
- `pause()` / `resume()` are similarly idempotent and only fire their `on_*` hook on an actual state change.
- `cleanup()` destroys every object, clears the collision system's active contacts (without firing exit callbacks), and returns the scene to an uninitialized state so it could — in principle — be initialized again.

## Deferred Object Mutation

`add_object()` and `remove_object()` can be called at any time, including from inside a `GameObject.update()` or a collision callback fired during `Scene.update()`. If called while the scene is mid-update, the mutation is queued and applied once that update finishes:

```python
def update(self, delta_time):
    super().update(delta_time)
    if self.health <= 0:
        self.scene.remove_object(self)  # safe even mid-iteration
```

Objects added during an update start on the *next* update, not the current one. `Scene.is_object_pending_removal(obj)` lets other systems (the collision system uses this) check whether an object is already on its way out before treating it as live.

## Persistent Objects

An object can be marked to survive a scene *replacement* — for example, a player or a running score tracker that should carry over from gameplay into a game-over scene:

```python
player.set_persistent()
```

When `SceneManager.replace_now()` swaps scenes, persistent objects are detached from the old scene *before* it is cleaned up, then reattached to the new scene without re-running `on_start()` or restarting their components — they were already started, and `_ensure_started()` is a no-op on anything already marked started.

Two safeguards run before anything is torn down:

- Persistent objects must have unique, non-empty names.
- A persistent object's name must not already exist in the destination scene.

Either violation raises `ValueError` and leaves the source scene completely untouched — nothing is destroyed if the transfer can't succeed cleanly.

## SceneManager

`SceneManager` owns a named registry and a scene stack. `GameEngine` creates one automatically; you can also use it directly.

```python
from engine import GameEngine, Scene

class MyGame(GameEngine):
    def initialize(self):
        self.register_scene('menu', MenuScene)          # zero-arg factory
        self.register_scene('game', lambda: GameScene(seed=1))
        self.load_scene('menu')
```

A registered provider can be a `Scene` instance (reused every time) or a zero-argument callable that returns a fresh `Scene` — use a factory whenever a scene needs to reset its own state each time it's entered.

### Immediate vs. Deferred

`load_scene()`, `push_scene()`, and `pop_scene()` **queue** a transition; it applies at the start of the next `process_pending()` call, which `GameEngine.run()` invokes once per frame. This keeps a transition requested mid-update from mutating the scene stack out from under the code that's still iterating over it.

`SceneManager.replace_now()`, `push_now()`, and `pop_now()` apply immediately, for tooling or tests that don't need the deferral.

### Scene Stack Semantics

- Only the top scene updates.
- All stacked scenes render, bottom to top.
- Pushing pauses the scene beneath the new overlay.
- Popping cleans up the top scene and resumes the one below it.
- Replacing cleans up the current scene before initializing its replacement.
- `load_scene()` means "replace the current scene" — it does not stack.

```python
self.push_scene('pause')   # gameplay pauses, pause menu renders on top
...
self.pop_scene()           # pause menu is destroyed, gameplay resumes
```

## GameEngine Integration and Backward Compatibility

`current_scene` and `load_scene(scene)` still work exactly as before — existing games needed no changes. `current_scene` also accepts a direct `Scene` assignment before `run()` starts, matching the original API.

`current_scene` keeps returning the last active scene even after the engine has fully shut down (`run()` has returned), so code that inspects final scene state after the loop exits — logging, a test harness, a wrapper script — doesn't have to guard against `None`. Internally, the scene stack itself is genuinely emptied and every scene on it is cleaned up; `GameEngine` just remembers what was on top immediately before that happened.

New methods, all backed by the same `SceneManager`:

- `register_scene(name, provider, replace=False)`
- `load_scene(scene_or_name)` — replace
- `push_scene(scene_or_name)` — stack an overlay
- `pop_scene()` — remove the top overlay

## Reference Implementation

`examples/games/ui_game.py` is the reference implementation: `MenuScene`, `GameScene`, and `GameOverScene` are registered by name, and a `PauseScene` demonstrates the stack — pressing Escape during gameplay pushes a pause overlay (gameplay visibly freezes underneath it), and either button on the overlay pops it or replaces the whole stack back to the menu.

```bash
python -m examples.games.ui_game
```

## Current Scope

- Scenes are cleaned up top-to-bottom on `SceneManager.clear()`; nothing currently persists across a full engine shutdown except through `GameEngine.current_scene`'s post-shutdown fallback described above.
- There is no scene transition animation or crossfade support — a replace or pop is instantaneous.
- A pushed scene must not already be present elsewhere in the stack; pushing a scene object that's already stacked raises `ValueError`.
