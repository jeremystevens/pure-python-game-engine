# Engine Architecture Decision

- **Status:** Accepted
- **Date:** September 26, 2026

## Decision

The `Scene` → `GameObject` → `Component` model is the primary, supported architecture for games built with this engine.

The Entity Component System under `engine.ecs` remains available as an experimental subsystem for learning, prototyping, and measuring data-oriented approaches. It is not the internal implementation of `GameObject`, and the two models are not automatically synchronized.

## Why GameObject Is Primary

- Every complete example game already uses `Scene`, `GameObject`, and components.
- The model integrates directly with transforms, sprites, rendering, input, and scene lifecycle callbacks.
- It provides a small, approachable API that fits the project's educational goals.
- Keeping the working model avoids an unnecessary rewrite before profiling identifies a concrete limitation.

New games should begin with imports from the stable top-level API:

```python
from engine import Component, GameEngine, GameObject, Scene, Sprite, Vector2
```

The complete games under `examples/games/` are the reference implementations for this architecture.

## Experimental ECS Boundary

ECS APIs must be imported explicitly from `engine.ecs` or one of its submodules. They are intentionally not re-exported from the top-level `engine` package:

```python
from engine.ecs.world import World
from engine.ecs.components import TransformComponent, VelocityComponent
from engine.ecs.systems import MovementSystem
```

The ECS demonstration is available with:

```bash
python -m examples.demos.ecs
```

Experimental means:

- ECS behavior remains covered by automated tests.
- The subsystem may evolve without the same compatibility guarantees as the primary API.
- New engine features do not need parallel GameObject and ECS implementations by default.
- ECS entities and GameObjects should not represent the same runtime object unless an explicit adapter is designed.
- No implicit synchronization exists between `Transform` and `TransformComponent`, scenes and worlds, or their lifecycle systems.

## Shared Foundations

Both models may use low-level, model-independent facilities such as:

- Vector and quaternion mathematics
- Rendering primitives
- Image assets, sprite atlases, and animation clips
- Input state
- Procedural audio
- Timing utilities

Shared facilities should not depend on either object model unless the dependency is essential.

## Consequences

- Engine development will prioritize GameObject components, scene management, collision handling, assets, and debugging tools.
- ECS remains in the repository and retains its focused demo and tests.
- The top-level `engine` exports define the primary public API.
- Experimental ECS types will not be added to top-level exports merely for convenience.
- Features should be implemented once for the primary architecture before considering an ECS equivalent.

## When to Reconsider

Revisit this decision only when there is evidence that the primary architecture is insufficient, such as:

- Profiling shows GameObject/component dispatch is a meaningful bottleneck.
- A game requires very large numbers of similarly structured entities.
- Multiple real games demonstrate a repeated need for data-oriented processing.
- An ECS migration plan can preserve or deliberately replace the existing public API.

Any future migration should begin with one small reference game, preferably Breakout, and include benchmarks, compatibility notes, and a staged transition plan.
