# Collision System

The engine provides scene-managed 2D overlap detection for the primary GameObject/component architecture. It detects contacts and reports their lifecycle; game code remains responsible for responses such as bouncing, damage, scoring, or object destruction.

## Collider Components

Use `PointCollider` for point-like objects, `CircleCollider` for circular objects, and `AABBCollider` for axis-aligned rectangles:

```python
from engine import AABBCollider, CircleCollider, GameObject, PointCollider, Vector2

cursor = GameObject('Cursor')
cursor.add_component(PointCollider())

ball = GameObject('Ball')
ball_collider = ball.add_component(CircleCollider(radius=4))

brick = GameObject('Brick')
brick_collider = brick.add_component(AABBCollider(Vector2(40, 16)))
```

Collider geometry follows the GameObject's world position and scale. An optional local offset is transformed into world space:

```python
hitbox = CircleCollider(radius=8, offset=Vector2(5, 0))
```

Circle radii use the largest absolute world-scale component. AABB width and height use the corresponding absolute world-scale components. AABBs remain axis-aligned and do not rotate with the GameObject.

## Collision Events

Register callbacks directly on a collider. Each callback receives the other collider:

```python
def hit_enemy(other):
    enemy = other.game_object
    enemy.destroy()

ball_collider.on_enter(hit_enemy)
ball_collider.on_stay(lambda other: print('still touching', other.game_object.name))
ball_collider.on_exit(lambda other: print('separated from', other.game_object.name))
```

- **Enter:** first update in which the pair touches or overlaps
- **Stay:** each additional update while contact continues
- **Exit:** first update after the contact ends or becomes filtered out

Callbacks can be removed with `remove_enter_callback`, `remove_stay_callback`, and `remove_exit_callback`.

## Layers and Masks

Layers and masks are integer bit fields. A pair is considered only when each collider's mask includes the other collider's layer:

```python
BALL = 1 << 0
PADDLE = 1 << 1
BRICK = 1 << 2

ball = CircleCollider(4, layer=BALL, mask=PADDLE | BRICK)
paddle = AABBCollider(Vector2(64, 12), layer=PADDLE, mask=BALL)
brick = AABBCollider(Vector2(40, 16), layer=BRICK, mask=BALL)
```

The default mask includes all 32 conventional layer bits. A layer or mask of zero disables contact from that side.

## Scene Lifecycle

Every `Scene` owns a `collision_system`. Collision detection runs automatically after GameObjects update and before destroyed objects are removed.

The system uses a stable collider snapshot for each update:

- Objects added by a collision callback become eligible on the next update.
- Objects destroyed or removed by a callback are handled safely.
- Inactive or destroyed GameObjects and inactive collider components are ignored.
- Colliders attached to the same GameObject do not collide with one another.
- Scene cleanup discards active contacts without firing teardown callbacks.

## Geometry Queries

Low-level geometry primitives and tests are available from `engine.collision`:

```python
from engine.collision import AABB, Circle, circle_intersects_aabb

circle = Circle(Vector2(10, 10), 5)
box = AABB.from_size(Vector2(15, 10), Vector2(8, 8))
if circle_intersects_aabb(circle, box):
    print('overlap')
```

Available queries include point-circle, point-AABB, circle-circle, AABB-AABB, and circle-AABB tests. Touching boundaries count as contact.

## Current Scope

The initial implementation intentionally favors clarity:

- Detection is non-physical; there is no automatic movement or penetration correction.
- AABBs do not account for rotation.
- Broad-phase detection currently checks collider pairs directly.
- Spatial hashing and debug visualization are deferred until profiling or tooling work justifies them.

Breakout under `examples/games/breakout_game.py` is the first complete reference game migrated to this system.
