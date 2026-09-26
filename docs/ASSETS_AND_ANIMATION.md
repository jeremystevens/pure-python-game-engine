# Assets and Animation

The engine includes a standard-library-only image cache, sprite-sheet atlas, and reusable animation system. It uses Tkinter `PhotoImage`, so no Pillow or other runtime dependency is required.

## Asset Manager

Every `GameEngine` owns an `asset_manager`. Configure its root when constructing the engine:

```python
from pathlib import Path
from engine import GameEngine

class MyGame(GameEngine):
    def __init__(self):
        super().__init__(asset_root=Path(__file__).parent / 'assets')
```

Relative paths resolve from that root. Absolute paths are also accepted:

```python
player_image = self.asset_manager.load_image('player.png')
```

Loading the same canonical path again returns the same image object:

```python
assert self.asset_manager.load_image('player.png') is player_image
```

The manager supports PNG, GIF, PGM, and PPM files—the formats supported by modern Tkinter without external packages. Missing files, unsupported extensions, and decoding failures raise specific errors from `engine.assets`.

Useful methods:

- `load_image(path, reload=False)` loads or retrieves a cached image.
- `get_image(path)` returns an already cached image or `None`.
- `is_image_loaded(path)` checks the cache.
- `unload(path)` releases one cached reference.
- `clear()` releases all cached references.
- `loaded_image_paths()` returns a snapshot of canonical cached paths.

The engine clears its image cache during shutdown, including exceptional exits.

## Direct Image Sprites

A `Sprite` can render a cached image directly:

```python
from engine import GameObject, Sprite

player = GameObject('Player')
player.add_component(Sprite(image=player_image))
```

Calling `sprite.set_image(None)` restores geometric fallback rendering. Tkinter images currently render at their native pixel dimensions and are positioned by the GameObject transform. Image rotation, arbitrary scaling, tinting, and alpha processing are outside the current standard-library renderer scope.

## Sprite Atlases

A `SpriteAtlas` maps names to whole-pixel regions of a source image:

```python
from engine import SpriteAtlas, Vector2

sheet = self.asset_manager.load_image('characters.png')
atlas = SpriteAtlas(Vector2(320, 64), sheet)
frame_names = atlas.create_animation_frames(
    'walk',
    frame_count=5,
    frame_size=Vector2(64, 64),
    start_position=Vector2.zero(),
    horizontal=True,
)
```

Frames are extracted lazily and cached when first rendered. Region replacement invalidates only that region's cached frame. `clear_frames()` releases extracted frames while retaining region definitions.

Atlas regions must:

- Have non-empty names
- Use non-negative, whole-pixel positions
- Have positive, whole-pixel dimensions
- Fit entirely inside the declared texture size

Atlases without a source image remain useful as colored-region metadata for backward-compatible shape rendering.

## Animation Clips

`AnimationClip` is immutable and shareable. Each Sprite creates independent playback state from the clip:

```python
from engine import AnimationClip

walk = AnimationClip.from_frames(
    'walk',
    frame_names,
    frame_duration=0.12,
    loop=True,
)

sprite.add_animation_clip(walk)
sprite.play_animation('walk')
```

A clip can use named atlas regions or numeric legacy frame indices. Animation updates preserve fractional frame time and can advance across multiple frames after a large delta.

Playback controls:

- `play_animation(name, reset=True)`
- `pause_animation()`
- `resume_animation()`
- `stop_animation()`

Non-looping animations stop on their final frame. Optional completion callbacks run once when a non-looping clip finishes and once per completed cycle for looping clips.

## Demo

Run the complete demo from the repository root:

```bash
python -m examples.demos.atlas
```

The demo uses `examples/assets/pulse_sprite_sheet.png`, a repository-owned 320 × 64 RGBA sprite sheet generated for this project. It demonstrates:

- Loading a real PNG
- Cache identity reuse
- Displaying the original sprite sheet
- Lazy extraction of five atlas regions
- Three independent players sharing one immutable clip
- Pause, resume, and restart controls

Controls:

- **Space:** Pause or resume all animations
- **R:** Restart all animations
- **Escape:** Quit
