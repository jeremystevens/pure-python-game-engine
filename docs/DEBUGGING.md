# Debugging Tools

Every `GameEngine` owns a `DebugOverlay` (`self.debug_overlay`) automatically — no setup required, and no existing game needed to change anything to get it. It's driven entirely by four function keys, checked once per frame before game update logic runs.

| Key | Effect |
| --- | --- |
| **F3** | Toggle the stats overlay (FPS, frame time, object/collider counts, scene info) |
| **F4** | Toggle collider outlines, drawn over every active `Collider` in the current scene |
| **F5** | Cycle the global log level: `WARNING → ERROR → DEBUG → INFO → …` |
| **F6** | Log a snapshot of the current scene's objects to the console |

All four are independent — enabling one doesn't affect the others, and everything is off by default.

## Stats Overlay (F3)

Drawn in the top-left corner:

```
FPS: 60.0   Frame: 16.4ms (min 15.9 / max 24.1)
Scene: Game   Stack depth: 1
Objects: 12 (11 active)   Colliders: 9
Log level: INFO
F3 stats  F4 colliders  F5 log level  F6 inspect scene
```

Frame time is computed from the last 120 real (unbounded) frame durations — not the engine's smoothed, stall-capped `delta_time` — so it reflects actual rendering cost, including any hitches.

## Collider Visualization (F4)

Draws a green outline over the world-space shape of every active `Collider` component in the current scene: a circle for `CircleCollider`/`PointCollider`, a rectangle for `AABBCollider`. Point colliders (zero radius) are drawn with a minimum 1-pixel radius so they stay visible. This reuses the same `collider.shape` property the collision system itself uses for detection, so what you see is exactly what's being tested for overlap.

## Runtime Log Level (F5)

Cycles the process-wide log level via the existing `engine.core.logger` module (`set_global_log_level`). The confirmation message is logged *at the new level itself* — logging it at `.info()` would silently vanish the moment you raise the level above `INFO`.

## Scene Inspection (F6)

Logs the current scene's name, total and active object counts, and then one line per object: name, position, active state, tags, and the list of component class names attached to it.

```
[Debug] [INFO] Scene 'Game': 12 object(s), 11 active
[Debug] [INFO]   'Ball_3' pos=(214.2, 88.9) active=True tags=[] components=['Sprite', 'CircleCollider']
```

## Slow-Frame Warnings (automatic, no key)

Every frame's real duration is recorded automatically. If a frame takes more than `DebugOverlay.SLOW_FRAME_MULTIPLIER` (2×, by default) the target frame time, a warning is logged without any input needed:

```
[Debug] [WARNING] Slow frame: 41.2ms (target 16.7ms)
```

This makes an unexpected stall visible in the console immediately, whether or not the stats overlay is open.

## Demo

```bash
python -m examples.demos.debug_tools
```

Bouncing circle colliders, two static box colliders, and a deliberate periodic hitch (to trigger the slow-frame warning on cue) give all four tools something worth looking at immediately.

## Current Scope

- The overlay and collider outlines only draw for the *current* scene — a paused scene beneath a pushed overlay isn't inspected (only what's actually rendering into `current_scene` at the moment F3/F4 are active).
- There's no interactive object picking or live property editing — inspection is a one-shot console dump (F6), not a persistent panel.
- AABB collider outlines don't rotate, matching the collision system's own AABB limitation (see `docs/COLLISION.md`).
