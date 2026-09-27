# Game Developer Guide

A single, self-contained walkthrough for building a game with this engine — ordered the way you'd actually build one, not alphabetized by subsystem. Every code sample below is copy-pasteable and has been run against the real engine.

This guide covers the *common path*. For depth on any one system — full API surface, edge cases, current limitations — the per-subsystem docs remain the backup reference: [`ARCHITECTURE.md`](ARCHITECTURE.md), [`COLLISION.md`](COLLISION.md), [`ASSETS_AND_ANIMATION.md`](ASSETS_AND_ANIMATION.md), [`AUDIO.md`](AUDIO.md), [`SCENE_MANAGEMENT.md`](SCENE_MANAGEMENT.md), [`DEBUGGING.md`](DEBUGGING.md). Nothing here duplicates them; it sequences and introduces the same ground.

## Table of Contents

1. [Setup & the Game Loop](#1-setup--the-game-loop)
2. [Your First GameObject](#2-your-first-gameobject)
3. [Making It Visible](#3-making-it-visible)
4. [Making It Move](#4-making-it-move)
5. [Custom Behavior: Components](#5-custom-behavior-components)
6. [Detecting Collisions](#6-detecting-collisions)
7. [Real Images (Optional)](#7-real-images-optional)
8. [Animation (Optional)](#8-animation-optional)
9. [Sound Effects](#9-sound-effects)
10. [Multiple Scenes](#10-multiple-scenes)
11. [Debugging Your Game](#11-debugging-your-game)
12. [Putting It All Together](#12-putting-it-all-together)
13. [Where to Go Next](#13-where-to-go-next)

Sections 1–6, 9, and 10 build one running example, **Dot Dodger**, incrementally — each section adds exactly one new capability to the same file. Sections 7 and 8 are shown as standalone snippets instead, since they need real image files this guide doesn't ship; they point to a runnable demo that has one.

---

## 1. Setup & the Game Loop

Every game is a subclass of `GameEngine`. Override `initialize()` to set up your game once, and `update(delta_time)` to run logic every frame:

```python
from engine import GameEngine

WIDTH, HEIGHT = 800, 600


class DotDodger(GameEngine):
    def initialize(self):
        print("Dot Dodger starting up")

    def update(self, delta_time: float):
        pass


if __name__ == "__main__":
    game = DotDodger("Dot Dodger", (WIDTH, HEIGHT))
    game.run()
```

Run it (as a module, from the repository root, so `engine` resolves): you'll get an empty 800×600 window titled "Dot Dodger" that closes normally.

A few things worth knowing before you build on this:

- `GameEngine(title, size, target_fps=60, max_delta_time=0.1)` — `target_fps` caps the frame rate; it isn't a fixed timestep. `delta_time` is measured with `time.perf_counter()`, smoothed over recent frames, and capped by `max_delta_time` so a stall (e.g. dragging the window) doesn't cause a huge simulation jump next frame.
- `run()` blocks until the window closes. It calls your `initialize()` once, then loops `update(delta_time)` → render → repeat.
- Every `GameEngine` already owns a `Scene`, an `InputManager`, an `AssetManager`, a `Renderer`, and a `DebugOverlay` — you never construct these yourself.

## 2. Your First GameObject

A `GameObject` is a container with a `Transform` (position, rotation, scale) and zero or more `Component`s attached to it. Add one to the engine's already-existing default scene, available as `self.current_scene`:

```python
from engine import GameEngine, GameObject, Vector2

WIDTH, HEIGHT = 800, 600


class DotDodger(GameEngine):
    def initialize(self):
        self.player = GameObject("Player")
        self.player.transform.position = Vector2(WIDTH / 2, HEIGHT / 2)
        self.current_scene.add_object(self.player)

    def update(self, delta_time: float):
        pass


if __name__ == "__main__":
    game = DotDodger("Dot Dodger", (WIDTH, HEIGHT))
    game.run()
```

Run it: still an empty window. That's expected — a bare `GameObject` has no visual representation. Position is real (you can inspect `self.player.transform.position`), it's just invisible.

## 3. Making It Visible

`Sprite` is a `Component` that renders a shape (or, later, an image). Add one to the player:

```python
from engine import GameEngine, GameObject, Sprite, Vector2

WIDTH, HEIGHT = 800, 600


class DotDodger(GameEngine):
    def initialize(self):
        self.player = GameObject("Player")
        self.player.transform.position = Vector2(WIDTH / 2, HEIGHT / 2)
        self.player.add_component(Sprite(color='#4FC3F7', size=Vector2(40, 40)))
        self.current_scene.add_object(self.player)

    def update(self, delta_time: float):
        pass


if __name__ == "__main__":
    game = DotDodger("Dot Dodger", (WIDTH, HEIGHT))
    game.run()
```

Run it: a light-blue 40×40 square sits in the middle of the window. `Sprite(color, size, shape='rectangle')` also accepts `shape='circle'` or `shape='triangle'`; every `GameObject`/`Component` pair works the same way — `add_component()` returns the component too, so you can capture a reference if you need to change its color or size later.

## 4. Making It Move

`self.input_manager` is available on every `GameEngine`. `get_movement_vector()` returns a normalized `Vector2` from either arrow keys or WASD (whichever is pressed):

```python
class DotDodger(GameEngine):
    def initialize(self):
        self.player = GameObject("Player")
        self.player.transform.position = Vector2(WIDTH / 2, HEIGHT / 2)
        self.player.add_component(Sprite(color='#4FC3F7', size=Vector2(40, 40)))
        self.current_scene.add_object(self.player)

    def update(self, delta_time: float):
        movement = self.input_manager.get_movement_vector()
        if movement.magnitude > 0:
            self.player.transform.translate(movement * 220 * delta_time)


if __name__ == "__main__":
    game = DotDodger("Dot Dodger", (WIDTH, HEIGHT))
    game.run()
```

Run it: arrow keys or WASD move the square at 220 pixels/second. Multiplying by `delta_time` is what makes that speed frame-rate independent — the same code runs at the same real-world speed whether the engine manages 30 FPS or 144 FPS. `transform.translate(delta)` just adds `delta` to the current position.

One problem: the square can now leave the visible window entirely. We'll fix that next — deliberately not inline in `update()`.

## 5. Custom Behavior: Components

You could patch the out-of-bounds check directly into `DotDodger.update()`. But logic that's really about *this object's* behavior belongs on the object, not on the engine — so it stays reusable and the engine class doesn't grow without bound as your game gets bigger. That's what subclassing `Component` is for:

```python
from engine import Component


class ScreenWrap(Component):
    """Wrap the game object back onto the screen when it exits the bounds."""

    def __init__(self, bounds: Vector2):
        super().__init__()
        self.bounds = bounds

    def update(self, delta_time: float):
        position = self.game_object.transform.position
        if position.x < 0:
            position.x = self.bounds.x
        elif position.x > self.bounds.x:
            position.x = 0
        if position.y < 0:
            position.y = self.bounds.y
        elif position.y > self.bounds.y:
            position.y = 0
```

Attach it in `initialize()`, alongside the `Sprite`:

```python
        self.player.add_component(ScreenWrap(Vector2(WIDTH, HEIGHT)))
```

Run it: walk off any edge and the player reappears on the opposite side. Every `Component` gets `start()` (once, the first frame it's active), `update(delta_time)` (every frame), `render(renderer)` (every frame, after `update`), and `destroy()` (when removed) — override whichever you need. `self.game_object` is always available inside a component, giving you back the object it's attached to.

## 6. Detecting Collisions

Add a second object — a goal to reach — and give both objects a `CircleCollider`:

```python
import random

from engine import CircleCollider

...

class DotDodger(GameEngine):
    def initialize(self):
        self.score = 0

        self.player = GameObject("Player")
        self.player.transform.position = Vector2(WIDTH / 2, HEIGHT / 2)
        self.player.add_component(Sprite(color='#4FC3F7', size=Vector2(40, 40)))
        self.player.add_component(ScreenWrap(Vector2(WIDTH, HEIGHT)))
        self.player.add_component(CircleCollider(radius=20, layer=1))
        self.current_scene.add_object(self.player)

        self.goal = GameObject("Goal")
        self.goal.add_component(Sprite(color='#66FF66', size=Vector2(24, 24), shape='circle'))
        goal_collider = self.goal.add_component(CircleCollider(radius=12, layer=2))
        self._place_goal()
        self.current_scene.add_object(self.goal)

        def on_goal_reached(other):
            self.score += 1
            print(f"Score: {self.score}")
            self._place_goal()

        goal_collider.on_enter(on_goal_reached)

    def _place_goal(self):
        self.goal.transform.position = Vector2(
            random.uniform(40, WIDTH - 40),
            random.uniform(40, HEIGHT - 40),
        )

    def update(self, delta_time: float):
        movement = self.input_manager.get_movement_vector()
        if movement.magnitude > 0:
            self.player.transform.translate(movement * 220 * delta_time)
```

Run it: walk into the green circle and the console prints an incrementing score, and the goal jumps to a new random spot.

A few things to note:

- Collision detection is fully automatic — any `Collider` attached to any `GameObject` in the active scene is checked every frame; there's no manual registration step.
- `on_enter(callback)` fires once, the first frame two colliders start overlapping. There's also `on_stay` (every frame they continue overlapping) and `on_exit` (the frame they stop). The callback receives the *other* collider, not its `GameObject` — use `other.game_object` if you need the object itself.
- `layer` and `mask` control which colliders can hit each other; the defaults (`mask=` "all layers") mean anything collides with anything, which is why this works without extra configuration. See [`COLLISION.md`](COLLISION.md) for filtering rules, `AABBCollider`, and the geometry helpers.

## 7. Real Images (Optional)

Everything so far has used flat-color shapes, which need no asset files. When you have your own artwork, `AssetManager` (`self.asset_manager` on every `GameEngine`) loads and caches PNG/GIF/PGM/PPM images, and `Sprite.set_image()` swaps a shape for an image:

```python
image = self.asset_manager.load_image('assets/player.png')
self.player.get_component(Sprite).set_image(image)
```

`load_image()` resolves relative paths against `asset_root` (the game's working directory by default, or whatever you pass as `GameEngine(..., asset_root=...)`), and returns the same cached image object on repeated calls for the same path — no need to track whether you've already loaded something. This snippet is standalone since Dot Dodger doesn't ship a PNG; see [`ASSETS_AND_ANIMATION.md`](ASSETS_AND_ANIMATION.md) for the full picture, including graceful handling of missing or unsupported files.

## 8. Animation (Optional)

Once you have a sprite sheet, `SpriteAtlas` slices it into named regions, and `AnimationClip` plays a sequence of them back:

```python
from engine import AnimationClip, SpriteAtlas

sheet = self.asset_manager.load_image('assets/characters.png')
atlas = SpriteAtlas(Vector2(320, 64), sheet)
frame_names = atlas.create_animation_frames('walk', 5, Vector2(64, 64), Vector2.zero())
clip = AnimationClip.from_frames('walk', frame_names, frame_duration=0.12)

sprite = self.player.get_component(Sprite)
sprite.set_sprite_atlas(atlas)
sprite.add_animation_clip(clip)
sprite.play_animation('walk')
```

`create_animation_frames(base_name, frame_count, frame_size, start_position)` adds `frame_count` evenly-spaced regions and returns their generated names, ready to hand to `AnimationClip.from_frames()`. Multiple sprites can share one `AnimationClip` while each keeps its own independent playback position — `add_animation_clip()` is what gives a sprite that independent state. Run `python -m examples.demos.atlas` for a working version of this against a real generated PNG. Full detail, including `pause`/`resume`/`stop` and completion callbacks, is in [`ASSETS_AND_ANIMATION.md`](ASSETS_AND_ANIMATION.md).

## 9. Sound Effects

Back to Dot Dodger. `SoundGenerator` computes real waveform samples with no sound files at all — `initialize_default_sounds()` registers three built-in effects (`"bullet"`, `"explosion"`, `"engine"`):

```python
from engine import SoundGenerator


class DotDodger(GameEngine):
    def initialize(self):
        self.sound_generator = SoundGenerator()
        self.sound_generator.initialize_default_sounds()

        # ... player, goal, colliders as before ...

        def on_goal_reached(other):
            self.score += 1
            print(f"Score: {self.score}")
            self.sound_generator.play_sound('bullet')
            self._place_goal()

        goal_collider.on_enter(on_goal_reached)
```

Run it: reaching the goal now also triggers a sound.

Be aware of what "sound" means here: **`play_sound()` does not send real audio to your speakers.** There's no way to do that cross-platform using only the standard library — `winsound` exists but is Windows-only, and this engine deliberately stays dependency-free rather than shell out to a platform player binary. Instead, `play_sound()` approximates each sound with the terminal bell (`\a`), timed and repeated based on how the sound was generated (a burst of beeps for noise-based effects, a single beep for continuous ones, and so on) — every beep is otherwise identical regardless of the sound's actual pitch. Full honesty about this gap, and exactly what differs sound to sound, is in [`AUDIO.md`](AUDIO.md).

## 10. Multiple Scenes

So far, everything — object creation, movement, scoring — has lived directly in `DotDodger`. That's fine for one continuous screen, but a menu and a pause overlay need separate `Scene`s that can be swapped or stacked. Here's the same game, reorganized:

```python
import random

from engine import (
    CircleCollider,
    Component,
    GameEngine,
    GameObject,
    Scene,
    Sprite,
    SoundGenerator,
    Vector2,
)

WIDTH, HEIGHT = 800, 600


class ScreenWrap(Component):
    def __init__(self, bounds: Vector2):
        super().__init__()
        self.bounds = bounds

    def update(self, delta_time: float):
        position = self.game_object.transform.position
        if position.x < 0:
            position.x = self.bounds.x
        elif position.x > self.bounds.x:
            position.x = 0
        if position.y < 0:
            position.y = self.bounds.y
        elif position.y > self.bounds.y:
            position.y = 0


class Label(GameObject):
    """A GameObject that renders text instead of a shape."""

    def __init__(self, name, text, position, color='#FFFFFF', font_size=20):
        super().__init__(name)
        self.text = text
        self.color = color
        self.font_size = font_size
        self.transform.position = position

    def render(self, renderer):
        renderer.draw_text(self.transform.position, self.text, self.color, self.font_size)


class MenuScene(Scene):
    def __init__(self):
        super().__init__("Menu")

    def on_initialize(self):
        self.add_object(Label("Title", "DOT DODGER", Vector2(WIDTH / 2, HEIGHT / 2 - 40), font_size=32))
        self.add_object(Label("Hint", "Press SPACE to start", Vector2(WIDTH / 2, HEIGHT / 2 + 20)))

    def update(self, delta_time: float):
        super().update(delta_time)
        if self.engine.input_manager.is_key_just_pressed('space'):
            self.engine.load_scene('game')


class GameScene(Scene):
    def __init__(self):
        super().__init__("Game")

    def on_initialize(self):
        self.score = 0

        self.player = GameObject("Player")
        self.player.transform.position = Vector2(WIDTH / 2, HEIGHT / 2)
        self.player.add_component(Sprite(color='#4FC3F7', size=Vector2(40, 40)))
        self.player.add_component(ScreenWrap(Vector2(WIDTH, HEIGHT)))
        self.player.add_component(CircleCollider(radius=20, layer=1))
        self.add_object(self.player)

        self.goal = GameObject("Goal")
        self.goal.add_component(Sprite(color='#66FF66', size=Vector2(24, 24), shape='circle'))
        goal_collider = self.goal.add_component(CircleCollider(radius=12, layer=2))
        self._place_goal()
        self.add_object(self.goal)

        self.score_label = Label("ScoreLabel", "Score: 0", Vector2(70, 24))
        self.add_object(self.score_label)

        def on_goal_reached(other):
            self.score += 1
            self.score_label.text = f"Score: {self.score}"
            self.engine.sound_generator.play_sound('bullet')
            self._place_goal()

        goal_collider.on_enter(on_goal_reached)

    def _place_goal(self):
        self.goal.transform.position = Vector2(
            random.uniform(40, WIDTH - 40),
            random.uniform(40, HEIGHT - 40),
        )

    def update(self, delta_time: float):
        super().update(delta_time)
        movement = self.engine.input_manager.get_movement_vector()
        if movement.magnitude > 0:
            self.player.transform.translate(movement * 220 * delta_time)


class PauseScene(Scene):
    def __init__(self):
        super().__init__("Pause")

    def on_initialize(self):
        self.add_object(Label("PauseTitle", "PAUSED", Vector2(WIDTH / 2, HEIGHT / 2 - 20), font_size=28))
        self.add_object(Label("PauseHint", "Press ESC to resume", Vector2(WIDTH / 2, HEIGHT / 2 + 20)))


class DotDodger(GameEngine):
    def initialize(self):
        self.sound_generator = SoundGenerator()
        self.sound_generator.initialize_default_sounds()

        self.register_scene('menu', MenuScene)
        self.register_scene('game', GameScene)
        self.register_scene('pause', PauseScene)
        self.load_scene('menu')

    def update(self, delta_time: float):
        if self.input_manager.is_key_just_pressed('escape'):
            scene_name = self.current_scene.name if self.current_scene else ""
            if scene_name == "Game":
                self.push_scene('pause')
            elif scene_name == "Pause":
                self.pop_scene()


if __name__ == "__main__":
    game = DotDodger("Dot Dodger", (WIDTH, HEIGHT))
    game.run()
```

What changed, and why:

- `register_scene(name, SceneClass)` registers a zero-argument factory — the class itself, since `MenuScene()` takes no extra arguments. `load_scene('menu')` looks it up by name and replaces the current scene with a fresh instance.
- Every `Scene` gets an `engine` attribute automatically once it's registered, loaded, or pushed — that's how `MenuScene.update()` can reach `self.engine.input_manager` and `self.engine.load_scene(...)`.
- `push_scene('pause')` pauses `GameScene` (its `update()` stops running, but it keeps rendering underneath) and initializes a fresh `PauseScene` on top. `pop_scene()` removes it and resumes what's beneath — this is exactly the "pause without losing game state" pattern.
- `self.sound_generator` lives on the engine, not a scene, so the same instance survives every scene switch instead of being rebuilt each time.

Full lifecycle ordering, stack semantics, and persistent-object rules (carrying an object across a scene replacement without destroying it) are in [`SCENE_MANAGEMENT.md`](SCENE_MANAGEMENT.md).

## 11. Debugging Your Game

Every `GameEngine` — this one included, with no setup — owns a `DebugOverlay` behind four function keys:

- **F3** — stats overlay: FPS, frame time, object/collider counts, current scene name
- **F4** — collider outlines, drawn over your existing sprites
- **F5** — cycle the global log level
- **F6** — dump the current scene's objects to the console

Slow frames are logged automatically as warnings, no key required. Run Dot Dodger and press F4 while chasing the goal — you'll see the `CircleCollider` radii drawn directly on top of the player and goal sprites, which is the fastest way to check a collision radius actually matches what you see on screen. Full key reference and current scope: [`DEBUGGING.md`](DEBUGGING.md).

## 12. Putting It All Together

The version at the end of [section 10](#10-multiple-scenes) is the complete, runnable Dot Dodger: a menu, movement, screen wrapping, collision-driven scoring, sound feedback, and a pause overlay, in about 100 lines. Save it as `dot_dodger.py` in the repository root and run it with `python dot_dodger.py`.

## 13. Where to Go Next

- Read the reference games in `examples/games/` — `breakout_game.py`, `asteroids_game.py`, `lane_crosser.py`, and others are not tutorials, but they show these same systems combined at full scale, including patterns this guide skipped (transform hierarchies, input profiles, persistent objects across scenes).
- Run the focused demos in `examples/demos/` for a single subsystem in isolation — `python -m examples.demos.atlas`, `python -m examples.demos.debug_tools`, `python -m examples.demos.scene_management`, and others.
- The per-subsystem docs linked throughout this guide cover everything left out here: collision layers/masks in depth, the full animation playback API, transform hierarchies and 3D/quaternion support, and the architectural decision behind why `GameObject`/`Component` — not the experimental ECS under `engine.ecs` — is the primary API.
