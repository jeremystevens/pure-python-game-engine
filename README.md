# Pure Python 2D Game Engine - Built Completely from Scratch

A comprehensive 2D game engine built entirely from scratch using **only Python's standard library**. No external dependencies like pygame, OpenGL, or any third-party graphics libraries. This engine demonstrates how to create a complete game development framework using pure Python and tkinter for cross-platform windowing.

## 🎯 Philosophy

This project proves that you can build sophisticated game engines without relying on external libraries. Every component - from vector mathematics to input handling to graphics rendering - is implemented from the ground up using only Python's built-in modules.

## ✨ Features

### Core Engine
- **Pure Python Implementation**: Zero external dependencies beyond Python standard library
- **Cross-Platform**: Uses tkinter for universal compatibility across Windows, macOS, and Linux
- **Game Engine Architecture**: Professional game engine design patterns and structure
- **Bounded Variable-Timestep Loop**: Responsive updates with smoothed, stall-safe delta time
- **Built-in Debugging Tools**: Stats overlay, collider visualization, log control, and scene inspection on every engine
- **2D/3D Hybrid Support**: Optional 3D mathematics with 2D rendering capabilities

### Scene System
- **Scene Management**: Organize game objects into scenes with deterministic lifecycle callbacks
- **Named Scene Registry & Stacking**: Register scenes by name and stack overlays for pause menus and dialogs
- **Persistent Objects**: Carry selected objects safely across scene replacements
- **GameObject Architecture**: Component-based game objects with transform hierarchy
- **Component System**: Modular components for extending game object functionality
- **Object Pooling**: Efficient memory management for game objects

### Mathematics (Built from Scratch)
- **Vector2**: Comprehensive 2D vector implementation with all standard operations
- **Vector3**: Full 3D vector mathematics with cross product, magnitude, and transformations
- **Transform System**: 2D/3D position, rotation, and scale with parent-child relationships
- **Quaternion Support**: 3D rotation support with quaternion mathematics (optional 3D mode)
- **Advanced Math**: Dot product, cross product, interpolation, and coordinate transformations
- **Collision Geometry**: Point, circle, and axis-aligned rectangle intersection queries

### Graphics Rendering
- **Custom 2D Renderer**: Built on tkinter Canvas with advanced drawing capabilities
- **Shape Rendering**: Rectangles, circles, triangles, and custom polygons
- **Transform Support**: Full rotation, scaling, and translation for all shapes
- **Color Management**: RGB color support with outline and fill options
- **Z-Ordering**: Proper layering system for depth sorting

### Input Handling
- **Keyboard Input**: Complete keyboard state management with key press detection
- **Mouse Input**: Mouse position, button states, and click detection
- **Input Utilities**: Convenience methods for common input patterns (WASD, arrows)
- **Event-Driven**: Proper event handling with frame-accurate input detection

### Audio System
- **Procedural Sound Generation**: Create sound effects using mathematical waveforms
- **Multiple Wave Types**: Support for sine, square, sawtooth, triangle, and noise waves
- **Sound Effects**: Built-in generators for bullets, explosions, and engine sounds
- **No External Dependencies**: Audio system built entirely with Python standard library
- **Real-time Playback**: Thread-based sound playback system

### Assets and Animation
- **Central Image Cache**: Canonical path resolution and identity reuse
- **Tkinter Image Rendering**: PNG, GIF, PGM, and PPM support without dependencies
- **Sprite Atlases**: Named regions with lazy frame extraction and caching
- **Reusable Animation Clips**: Shared clips with independent playback state
- **Playback Controls**: Play, pause, resume, stop, loop, and completion callbacks

## 🏗️ Project Structure

```
.
├── engine/                  # Game engine package
│   ├── assets/              # Image caching, atlases, and animation clips
│   ├── audio/               # Procedural sound generation
│   ├── collision/           # Collider components and overlap detection
│   ├── core/                # Main loop, window, and logging
│   ├── debug/               # Stats overlay, collider visualization, scene inspection
│   ├── ecs/                 # Experimental Entity Component System
│   ├── graphics/            # Canvas renderer and sprites
│   ├── input/               # Keyboard, mouse, and input profiles
│   ├── math/                # Vectors, transforms, and quaternions
│   └── scene/               # Scenes, GameObjects, components, and the SceneManager
├── examples/
│   ├── games/               # Complete playable games
│   └── demos/               # Focused engine feature demonstrations
├── tests/                   # Headless standard-library test suite
├── docs/                    # Project roadmap and supporting documents
├── README.md
└── LICENSE
```

## 🚀 Installation

**No installation required!** This engine uses only Python's standard library.

Requirements:
- Python 3.10 or higher (currently tested with Python 3.14)
- tkinter (included with most Python installations)

### Timing Model

The engine uses a bounded variable timestep. `target_fps` controls frame-rate limiting, elapsed time is measured with `time.perf_counter()`, and unusually long frames are capped at `0.1` seconds by default before delta smoothing. Games can customize the cap with `GameEngine(..., max_delta_time=...)`.

## 🧪 Running Tests

The headless test suite uses Python's standard-library `unittest` framework and does not open a game window:

```bash
python -m unittest discover -s tests -v
```

## 🎮 Quick Start

```python
from engine import GameEngine, GameObject, Vector2, Sprite, SoundGenerator

class MyGame(GameEngine):
    def initialize(self):
        # Initialize sound system
        self.sound_generator = SoundGenerator()
        self.sound_generator.initialize_default_sounds()
        
        # Create a game object
        player = GameObject("Player")
        player.transform.position = Vector2(400, 300)
        
        # Add a sprite component
        sprite = Sprite(color='#0096FF', size=Vector2(50, 50))
        player.add_component(sprite)
        
        # Add to scene
        self.current_scene.add_object(player)
    
    def update(self, delta_time):
        # Game logic here
        if self.input_manager.is_key_pressed('space'):
            self.sound_generator.play_sound("bullet")
            print("Space pressed!")

# Run the game
game = MyGame("My 2D Game", (800, 600))
game.run()
```

## 🎯 Examples

Run examples as modules from the repository root so Python can locate the sibling `engine` package.

### Complete Games

```bash
python -m examples.games.asteroids_game
python -m examples.games.breakout_game
python -m examples.games.centipede_game
python -m examples.games.space_shooter
python -m examples.games.ui_game
```

### Focused Demos

```bash
python -m examples.demos.basic_game
python -m examples.demos.atlas
python -m examples.demos.ecs
python -m examples.demos.input_profiles
python -m examples.demos.logging
python -m examples.demos.scene_management
python -m examples.demos.debug_tools
```

### Asteroids Controls

- **Left/Right or A/D**: Rotate ship
- **Up or W**: Thrust
- **Space or Ctrl**: Shoot
- **ESC**: Quit game

The examples demonstrate:
- Player movement with keyboard input
- Rotating enemies and physics simulation
- Real-time FPS display
- Component-based architecture
- Transform hierarchies
- Scene-managed collision events in Breakout
- **Procedural audio generation**
- Complete game state management

## 🔧 Architecture Overview

### Architectural Direction

The `Scene` → `GameObject` → `Component` model is the primary supported architecture and should be used for new games. The separate ECS under `engine.ecs` remains available for experimentation and its focused demo, but it is not re-exported from the top-level package or automatically synchronized with GameObjects.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full decision, boundaries, consequences, and criteria for reconsidering it.

### Primary GameObject Component System

The engine uses a component-based architecture where game objects are containers for components that define behavior:

```python
from engine import Component, GameObject, Sprite, Vector2

# Create a game object
player = GameObject("Player")

# Add components
player.add_component(Sprite(color='#FF0000'))
player.add_component(CustomBehavior())

# Components can access the game object
class CustomBehavior(Component):
    def update(self, delta_time):
        # Move the game object
        self.game_object.transform.translate(Vector2(100 * delta_time, 0))
```

### Transform Hierarchy
Supports parent-child relationships with automatic world space calculations:

```python
parent = GameObject("Parent")
child = GameObject("Child")

# Set up hierarchy
child.transform.parent = parent.transform

# Child position is relative to parent
child.transform.position = Vector2(50, 0)  # 50 units to the right of parent

# Optional 3D support
child.transform.enable_3d()
child.transform.quaternion_rotation = Quaternion.from_axis_angle(Vector3.up(), math.pi/4)
```

### Assets and Animation

Each game owns an `AssetManager` for loading and caching Tk-compatible images. Sprites can render images directly or select lazily extracted atlas frames driven by reusable animation clips:

```python
from engine import AnimationClip, SpriteAtlas, Vector2

sheet = self.asset_manager.load_image('assets/characters.png')
atlas = SpriteAtlas(Vector2(320, 64), sheet)
frames = atlas.create_animation_frames(
    'walk', 5, Vector2(64, 64), Vector2.zero()
)
clip = AnimationClip.from_frames('walk', frames, 0.12)
```

See [`docs/ASSETS_AND_ANIMATION.md`](docs/ASSETS_AND_ANIMATION.md) and run `python -m examples.demos.atlas` for the real PNG demo.

### Collision System

Scenes automatically detect contacts between `CircleCollider` and `AABBCollider` components. Layers and masks filter pairs, while enter, stay, and exit callbacks let games define their own responses:

```python
from engine import CircleCollider

collider = player.add_component(CircleCollider(radius=12))
collider.on_enter(lambda other: print(f"Hit {other.game_object.name}"))
```

See [`docs/COLLISION.md`](docs/COLLISION.md) for geometry queries, layer configuration, lifecycle behavior, and current limitations. Breakout is the first complete reference game using the system.

### Scene Management

A `SceneManager` gives every `GameEngine` a named scene registry and a scene stack, on top of the existing `Scene` lifecycle (deferred object mutation, pause/resume, persistent objects across replacements):

```python
self.register_scene('menu', MenuScene)
self.register_scene('game', GameScene)
self.load_scene('menu')       # replace the current scene
self.push_scene('pause')      # stack a paused overlay on top
self.pop_scene()              # remove the overlay, resume what's beneath
```

`current_scene` and `load_scene(scene)` still work exactly as before, so no existing game needed changes. See [`docs/SCENE_MANAGEMENT.md`](docs/SCENE_MANAGEMENT.md) for lifecycle ordering, stack semantics, and persistent-object rules. `examples/games/ui_game.py` is the reference implementation, including a pushed `PauseScene`.

### Debugging Tools

Every `GameEngine` owns a `DebugOverlay` automatically — no setup, and no existing game needed to change anything:

```python
# F3 stats overlay | F4 collider outlines | F5 cycle log level | F6 inspect scene
```

Slow frames are logged automatically too, with no key required:

```
[Debug] [WARNING] Slow frame: 41.2ms (target 16.7ms)
```

See [`docs/DEBUGGING.md`](docs/DEBUGGING.md) for the full key reference and current scope, and run `python -m examples.demos.debug_tools` for bouncing colliders plus a deliberate periodic hitch to see the slow-frame warning fire on cue.

### Pure Python Rendering
Custom 2D renderer built on tkinter Canvas:

```python
# The renderer can draw various shapes
renderer.draw_rectangle(position, size, color='#FF0000', rotation=math.pi/4)
renderer.draw_circle(position, radius, color='#00FF00')
renderer.draw_polygon(points, color='#0000FF')
```

## 🎨 Advanced Features

### Custom Components
Extend the Component class to create custom behaviors:

```python
class HealthComponent(Component):
    def __init__(self, max_health=100):
        super().__init__()
        self.max_health = max_health
        self.current_health = max_health
    
    def take_damage(self, damage):
        self.current_health = max(0, self.current_health - damage)
        if self.current_health == 0:
            self.game_object.destroy()
```

### Input Handling
Comprehensive input system with multiple access patterns:

```python
# In your game update loop
if input_manager.is_key_just_pressed('space'):
    player.jump()

# Get normalized movement vector
movement = input_manager.get_movement_vector()
player.transform.translate(movement * speed * delta_time)
```

### Vector Mathematics
Rich 2D and 3D vector systems with all standard operations:

```python
# 2D Vector operations
velocity = Vector2(100, 50)
acceleration = Vector2(0, -9.8)
velocity += acceleration * delta_time

# 3D Vector operations
position_3d = Vector3(10, 20, 30)
direction_3d = Vector3.forward()
cross_product = position_3d.cross(direction_3d)

# Advanced operations
distance = player_pos.distance_to(enemy_pos)
direction = (target_pos - current_pos).normalize()
rotated = velocity.rotate(math.pi / 4)
```

### Procedural Audio System
Generate sound effects using mathematical waveforms:

```python
from engine import SoundGenerator

# Initialize sound system
sound_gen = SoundGenerator()

# Create custom sounds
bullet_sound = sound_gen.create_bullet_sound()
explosion_sound = sound_gen.create_explosion_sound()
engine_sound = sound_gen.create_engine_sound()

# Register and play sounds
sound_gen.register_sound(bullet_sound)
sound_gen.play_sound("bullet")

# Or use built-in sounds
sound_gen.initialize_default_sounds()
sound_gen.play_sound("explosion")
```

### Scene Management
Organize your game into named scenes, with stacked overlays for menus and pause screens:

```python
self.register_scene("menu", MenuScene)
self.register_scene("game", GameScene)

# Switch between scenes by name
self.load_scene("game")

# Or stack an overlay without tearing down what's underneath
self.push_scene("pause")
self.pop_scene()
```

See [`docs/SCENE_MANAGEMENT.md`](docs/SCENE_MANAGEMENT.md) for the full lifecycle, stack semantics, and persistent-object rules.

## 🎯 Why Pure Python?

This project demonstrates several important concepts:

1. **Understanding Fundamentals**: Building from scratch teaches you how game engines actually work
2. **No Dependencies**: Eliminates external library conflicts and licensing concerns
3. **Educational Value**: Perfect for learning game development concepts
4. **Portability**: Runs anywhere Python runs, no additional installations
5. **Customization**: Complete control over every aspect of the engine

## 🚀 Performance Considerations

This engine prioritizes education and simplicity over speculative optimization. Current safeguards include:

- **Bounded Frame Timing**: Prevents large simulation jumps after stalls
- **Squared-Distance Geometry**: Avoids square roots where only overlap is needed
- **Collision Layer Filtering**: Rejects disallowed pairs before geometry tests
- **Snapshot-Safe Updates**: Allows callbacks to add or destroy objects safely
- **Asset Caching**: Reuses decoded images and extracted atlas frames

Collision broad-phase detection currently checks collider pairs directly. Object pooling and spatial partitioning are intentionally deferred until profiling demonstrates a need.

## 🎓 Learning Outcomes

By studying this engine, you'll learn:

- Game engine architecture and design patterns
- 2D and 3D mathematics and coordinate systems
- Vector mathematics and quaternion rotations
- Component-based entity systems
- Input handling and event processing
- 2D graphics rendering techniques
- Transform hierarchies and world/local space conversions
- Scene management and state machines
- Image caching, sprite atlases, and frame animation
- **Procedural audio generation and waveform synthesis**
- **Mathematical sound effect creation**
- Performance optimization techniques

## 🤝 Contributing

This project is designed for educational purposes. Contributions that improve the learning experience or add well-documented features are welcome!

## 📄 License

This project is open source and available under the MIT License.

---

**Built with ❤️ using only Python's standard library**